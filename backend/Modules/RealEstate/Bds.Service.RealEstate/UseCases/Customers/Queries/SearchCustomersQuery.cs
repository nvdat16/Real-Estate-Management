using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Queries;

public sealed record SearchCustomersQuery(string? Keyword, PageOptions Paging)
    : IRequest<PagedResult<CustomerResponse>>, IPagedQuery;
