using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Commands;

public sealed record CreateProjectCommand(
    string Code,
    string Name,
    Guid ProvinceId,
    Guid DistrictId,
    string AddressLine,
    string Developer) : IRequest<ProjectResponse>;
