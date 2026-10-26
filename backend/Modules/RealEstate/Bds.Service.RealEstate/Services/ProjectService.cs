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

public sealed class ProjectService(IProjectRepository projectRepository) : IProjectService
{
    public async Task<ProjectResponse> CreateAsync(CreateProjectCommand command, CancellationToken cancellationToken)
    {
        var project = Project.Create(command.Code, command.Name, command.ProvinceId, command.DistrictId, command.AddressLine, command.Developer);

        var result = await projectRepository.CreateAsync(project, cancellationToken);
        ProjectRules.EnsureSuccess(result);

        return await GetByIdAsync(new GetProjectByIdQuery(project.Id), cancellationToken);
    }

    public async Task<ProjectResponse> UpdateAsync(UpdateProjectCommand command, CancellationToken cancellationToken)
    {
        var status = Enum.Parse<ProjectStatus>(command.Status, ignoreCase: true);

        var result = await projectRepository.UpdateAsync(
            command.Id,
            command.Name.Trim(),
            command.ProvinceId,
            command.DistrictId,
            command.AddressLine.Trim(),
            command.Developer.Trim(),
            status,
            cancellationToken);
        ProjectRules.EnsureSuccess(result);

        return await GetByIdAsync(new GetProjectByIdQuery(command.Id), cancellationToken);
    }

    public async Task DeleteAsync(DeleteProjectCommand command, CancellationToken cancellationToken)
    {
        var result = await projectRepository.DeleteAsync(command.Id, cancellationToken);
        ProjectRules.EnsureSuccess(result);
    }

    public async Task<ProjectResponse> GetByIdAsync(GetProjectByIdQuery query, CancellationToken cancellationToken)
    {
        var project = await projectRepository.GetByIdAsync(query.Id, cancellationToken)
            ?? throw AppException.NotFound(ProjectRules.NotFoundMessage);

        return ProjectMapping.ToResponse(project);
    }

    public async Task<PagedResult<ProjectResponse>> SearchAsync(SearchProjectsQuery query, CancellationToken cancellationToken)
    {
        var status = query.Status is null ? (ProjectStatus?)null : Enum.Parse<ProjectStatus>(query.Status, ignoreCase: true);
        var filter = new ProjectFilter(
            query.Keyword, query.ProvinceId, query.DistrictId, status, query.SortBy, query.Descending, query.Page, query.PageSize);

        var (items, totalCount) = await projectRepository.SearchAsync(filter, cancellationToken);
        return new PagedResult<ProjectResponse>(
            items.Select(ProjectMapping.ToResponse).ToList(), query.Page, query.PageSize, totalCount);
    }
}
