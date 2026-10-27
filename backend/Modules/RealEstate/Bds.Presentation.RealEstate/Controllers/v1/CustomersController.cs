using Bds.BuildingBlocks.Application.Models;
using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.RealEstate.Requests;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Customers.Commands;
using Bds.Service.RealEstate.UseCases.Customers.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.RealEstate.Controllers.v1;

[ApiController]
[Route("api/v1/customers")]
public sealed class CustomersController(IMediator mediator) : ControllerBase
{
    [HttpGet("me")]
    [Authorize(Policy = Permissions.ProfileCustomer)]
    public async Task<ActionResult<CustomerResponse>> GetMe(CancellationToken cancellationToken) =>
        await mediator.Send(new GetMyCustomerProfileQuery(User.GetUserId()), cancellationToken);

    [HttpPut("me")]
    [Authorize(Policy = Permissions.ProfileCustomer)]
    public async Task<ActionResult<CustomerResponse>> UpsertMe(UpsertCustomerProfileRequest request, CancellationToken cancellationToken)
    {
        var command = new UpsertCustomerProfileCommand(
            User.GetUserId(), User.GetEmail(), request.FullName, request.PhoneNumber, request.DateOfBirth, request.Address);
        return await mediator.Send(command, cancellationToken);
    }

    [HttpGet]
    [Authorize(Policy = Permissions.CustomersManage)]
    public async Task<ActionResult<PagedResult<CustomerResponse>>> Search(
        [FromQuery] SearchCustomersRequest request,
        CancellationToken cancellationToken)
    {
        var paging = new PageOptions(request.Page, request.PageSize, request.SortBy, request.Descending);
        return await mediator.Send(new SearchCustomersQuery(request.Keyword, paging), cancellationToken);
    }

    [HttpGet("{id:guid}")]
    [Authorize(Policy = Permissions.CustomersManage)]
    public async Task<ActionResult<CustomerResponse>> GetById(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new GetCustomerByIdQuery(id), cancellationToken);
}
