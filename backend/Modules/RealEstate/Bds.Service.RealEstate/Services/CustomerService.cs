using Bds.BuildingBlocks.Application.Exceptions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.UseCases.Customers;
using Bds.Service.RealEstate.UseCases.Customers.Commands;
using Bds.Service.RealEstate.UseCases.Customers.Queries;

namespace Bds.Service.RealEstate.Services;

public sealed class CustomerService(ICustomerRepository customerRepository) : ICustomerService
{
    public async Task<CustomerResponse> UpsertProfileAsync(UpsertCustomerProfileCommand command, CancellationToken cancellationToken)
    {
        var customer = Customer.Create(
            command.UserId, command.Email, command.FullName, command.PhoneNumber, command.DateOfBirth, command.Address);
        await customerRepository.UpsertAsync(customer, cancellationToken);

        return await GetMyProfileAsync(new GetMyCustomerProfileQuery(command.UserId), cancellationToken);
    }

    public async Task<CustomerResponse> GetMyProfileAsync(GetMyCustomerProfileQuery query, CancellationToken cancellationToken)
    {
        var customer = await customerRepository.GetByUserIdAsync(query.UserId, cancellationToken)
            ?? throw AppException.NotFound("Bạn chưa có hồ sơ khách hàng.");

        return CustomerMapping.ToResponse(customer);
    }

    public async Task<CustomerResponse> GetByIdAsync(GetCustomerByIdQuery query, CancellationToken cancellationToken)
    {
        var customer = await customerRepository.GetByIdAsync(query.Id, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy khách hàng.");

        return CustomerMapping.ToResponse(customer);
    }

    public async Task<PagedResult<CustomerResponse>> SearchAsync(SearchCustomersQuery query, CancellationToken cancellationToken)
    {
        var (items, totalCount) = await customerRepository.SearchAsync(new ProfileFilter(query.Keyword, query.Paging), cancellationToken);
        return new PagedResult<CustomerResponse>(
            items.Select(CustomerMapping.ToResponse).ToList(), query.Paging.Page, query.Paging.PageSize, totalCount);
    }
}
