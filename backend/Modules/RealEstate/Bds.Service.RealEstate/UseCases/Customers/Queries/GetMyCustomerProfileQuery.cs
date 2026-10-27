using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Queries;

public sealed record GetMyCustomerProfileQuery(Guid UserId) : IRequest<CustomerResponse>;
