using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Queries;

public sealed record GetPropertyByIdQuery(Guid Id) : IRequest<PropertyResponse>;
