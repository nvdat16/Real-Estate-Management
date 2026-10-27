using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Queries.Handlers;

public sealed class GetMyCustomerProfileHandler(ICustomerService customerService)
    : IRequestHandler<GetMyCustomerProfileQuery, CustomerResponse>
{
    public Task<CustomerResponse> Handle(GetMyCustomerProfileQuery request, CancellationToken cancellationToken) =>
        customerService.GetMyProfileAsync(request, cancellationToken);
}
