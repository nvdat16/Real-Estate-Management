using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Commands;

public sealed record UpdateProjectCommand(
    Guid Id,
    string Name,
    Guid ProvinceId,
    Guid DistrictId,
    string AddressLine,
    string Developer,
    string Status) : IRequest<ProjectResponse>;
