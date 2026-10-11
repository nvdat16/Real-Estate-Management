using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;

namespace Bds.Service.RealEstate.UseCases.Projects;

public static class ProjectMapping
{
    public static ProjectResponse ToResponse(ProjectReadModel project) => new(
        project.Id,
        project.Code,
        project.Name,
        project.ProvinceId,
        project.ProvinceName,
        project.DistrictId,
        project.DistrictName,
        project.AddressLine,
        project.Developer,
        project.Status.ToString(),
        project.CreatedAt);
}
