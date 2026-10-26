using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Commands;

public sealed record UpdatePropertyCommand(
    Guid Id,
    decimal Area,
    int Floor,
    string Position,
    int Bedrooms,
    string Direction) : IRequest<PropertyResponse>;
