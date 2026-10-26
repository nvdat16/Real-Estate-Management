using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Commands;

public sealed record DeletePropertyCommand(Guid Id) : IRequest;
