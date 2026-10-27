using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Queries.Handlers;

public sealed class GetCustomerByIdHandler(ICustomerService customerService) : IRequestHandler<GetCustomerByIdQuery, CustomerResponse>
{
    public Task<CustomerResponse> Handle(GetCustomerByIdQuery request, CancellationToken cancellationToken) =>
        customerService.GetByIdAsync(request, cancellationToken);
}
