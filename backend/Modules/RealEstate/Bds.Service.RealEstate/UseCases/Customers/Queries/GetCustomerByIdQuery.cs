using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Queries;

public sealed record GetCustomerByIdQuery(Guid Id) : IRequest<CustomerResponse>;
