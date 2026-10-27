using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;

namespace Bds.Service.RealEstate.UseCases.Customers;

public static class CustomerMapping
{
    public static CustomerResponse ToResponse(CustomerReadModel customer) => new(
        customer.Id,
        customer.UserId,
        customer.FullName,
        customer.Email,
        customer.PhoneNumber,
        customer.DateOfBirth,
        customer.Address,
        customer.CreatedAt,
        customer.UpdatedAt);
}
