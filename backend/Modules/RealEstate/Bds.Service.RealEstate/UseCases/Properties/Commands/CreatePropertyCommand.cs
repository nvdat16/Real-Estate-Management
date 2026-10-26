using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Commands;

public sealed record CreatePropertyCommand(
    Guid ProjectId,
    string Code,
    decimal Area,
    int Floor,
    string Position,
    int Bedrooms,
    string Direction) : IRequest<PropertyResponse>;
