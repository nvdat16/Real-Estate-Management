using Bds.BuildingBlocks.Application.Exceptions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Entities;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.UseCases.Projects;
using Bds.Service.RealEstate.UseCases.Projects.Commands;
using Bds.Service.RealEstate.UseCases.Projects.Queries;

namespace Bds.Service.RealEstate.Services;

public sealed class ProjectService(
    IProjectRepository projectRepository,
    IProjectQueryRepository projectQueryRepository,
    ILocationQueryRepository locationQueryRepository,
    IRealEstateUnitOfWork unitOfWork) : IProjectService
{
    public async Task<ProjectResponse> CreateAsync(CreateProjectCommand command, CancellationToken cancellationToken)
    {
        var code = command.Code.Trim().ToUpperInvariant();
        if (await projectRepository.ExistsByCodeAsync(code, cancellationToken))
        {
            throw AppException.Conflict("Mã dự án đã tồn tại.");
        }

        await EnsureDistrictInProvinceAsync(command.DistrictId, command.ProvinceId, cancellationToken);

        var project = Project.Create(code, command.Name, command.ProvinceId, command.DistrictId, command.AddressLine, command.Developer);
        projectRepository.Add(project);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return await GetByIdAsync(new GetProjectByIdQuery(project.Id), cancellationToken);
    }

    public async Task<ProjectResponse> UpdateAsync(UpdateProjectCommand command, CancellationToken cancellationToken)
    {
        var project = await projectRepository.GetByIdAsync(command.Id, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy dự án.");

        await EnsureDistrictInProvinceAsync(command.DistrictId, command.ProvinceId, cancellationToken);

        var status = Enum.Parse<ProjectStatus>(command.Status, ignoreCase: true);
        project.Update(command.Name, command.ProvinceId, command.DistrictId, command.AddressLine, command.Developer, status);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return await GetByIdAsync(new GetProjectByIdQuery(project.Id), cancellationToken);
    }

    public async Task DeleteAsync(DeleteProjectCommand command, CancellationToken cancellationToken)
    {
        var project = await projectRepository.GetByIdAsync(command.Id, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy dự án.");

        project.Delete(DateTime.UtcNow);
        await unitOfWork.SaveChangesAsync(cancellationToken);
    }

    public async Task<ProjectResponse> GetByIdAsync(GetProjectByIdQuery query, CancellationToken cancellationToken)
    {
        var project = await projectQueryRepository.GetByIdAsync(query.Id, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy dự án.");

        return ProjectMapping.ToResponse(project);
    }

    public async Task<PagedResult<ProjectResponse>> SearchAsync(SearchProjectsQuery query, CancellationToken cancellationToken)
    {
        var status = query.Status is null ? (ProjectStatus?)null : Enum.Parse<ProjectStatus>(query.Status, ignoreCase: true);
        var filter = new ProjectFilter(
            query.Keyword, query.ProvinceId, query.DistrictId, status, query.SortBy, query.Descending, query.Page, query.PageSize);

        var (items, totalCount) = await projectQueryRepository.SearchAsync(filter, cancellationToken);
        return new PagedResult<ProjectResponse>(
            items.Select(ProjectMapping.ToResponse).ToList(), query.Page, query.PageSize, totalCount);
    }

    private async Task EnsureDistrictInProvinceAsync(Guid districtId, Guid provinceId, CancellationToken cancellationToken)
    {
        if (!await locationQueryRepository.DistrictBelongsToProvinceAsync(districtId, provinceId, cancellationToken))
        {
            throw AppException.BusinessRule("Quận/huyện không thuộc tỉnh/thành đã chọn.");
        }
    }
}
