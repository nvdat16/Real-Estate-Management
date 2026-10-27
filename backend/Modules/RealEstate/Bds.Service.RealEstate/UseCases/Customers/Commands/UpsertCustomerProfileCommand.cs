using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Commands;

public sealed record UpsertCustomerProfileCommand(
    Guid UserId,
    string Email,
    string FullName,
    string PhoneNumber,
    DateOnly? DateOfBirth,
    string? Address) : IRequest<CustomerResponse>;
