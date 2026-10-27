using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Commands.Handlers;

public sealed class UpsertCustomerProfileHandler(ICustomerService customerService)
    : IRequestHandler<UpsertCustomerProfileCommand, CustomerResponse>
{
    public Task<CustomerResponse> Handle(UpsertCustomerProfileCommand request, CancellationToken cancellationToken) =>
        customerService.UpsertProfileAsync(request, cancellationToken);
}
