using Bds.BuildingBlocks.Application.Models;
using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.RealEstate.Requests;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Listings.Commands;
using Bds.Service.RealEstate.UseCases.Listings.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.RealEstate.Controllers.v1;

[ApiController]
[Route("api/v1/listings")]
public sealed class ListingsController(IMediator mediator) : ControllerBase
{
    [HttpGet("public")]
    [AllowAnonymous]
    public async Task<ActionResult<PagedResult<ListingResponse>>> SearchPublic(
        [FromQuery] SearchPublicListingsRequest request,
        CancellationToken cancellationToken)
    {
        var query = new SearchPublicListingsQuery(
            request.Keyword, request.Type, request.MinPrice, request.MaxPrice, request.ProvinceId, request.DistrictId,
            request.ProjectId, request.MinArea, request.MaxArea, request.Bedrooms, ToPaging(request));
        return await mediator.Send(query, cancellationToken);
    }

    [HttpGet("mine")]
    [Authorize(Policy = Permissions.ListingsCreate)]
    public async Task<ActionResult<PagedResult<ListingResponse>>> SearchMine(
        [FromQuery] SearchListingsRequest request,
        CancellationToken cancellationToken)
    {
        var query = new SearchMyListingsQuery(User.GetUserId(), request.Keyword, request.Status, request.Type, ToPaging(request));
        return await mediator.Send(query, cancellationToken);
    }

    [HttpGet]
    [Authorize(Policy = Permissions.ListingsApprove)]
    public async Task<ActionResult<PagedResult<ListingResponse>>> Search(
        [FromQuery] SearchListingsRequest request,
        CancellationToken cancellationToken)
    {
        var query = new SearchListingsQuery(request.Keyword, request.Status, request.Type, ToPaging(request));
        return await mediator.Send(query, cancellationToken);
    }


    [HttpGet("{id:guid}")]
    [AllowAnonymous]
    public async Task<ActionResult<ListingResponse>> GetById(Guid id, CancellationToken cancellationToken)
    {
        Guid? currentUserId = User.Identity?.IsAuthenticated == true ? User.GetUserId() : null;
        var query = new GetListingByIdQuery(id, currentUserId, CanReview());
        return await mediator.Send(query, cancellationToken);
    }

    [HttpPost]
    [Authorize(Policy = Permissions.ListingsCreate)]
    public async Task<ActionResult<ListingResponse>> Create(CreateListingRequest request, CancellationToken cancellationToken)
    {
        var command = new CreateListingCommand(
            User.GetUserId(), request.PropertyId, request.Type, request.Price, request.Title, request.Description,
            request.ImageUrls ?? []);
        var listing = await mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetById), new { id = listing.Id }, listing);
    }

    [HttpPut("{id:guid}")]
    [Authorize(Policy = Permissions.ListingsCreate)]
    public async Task<ActionResult<ListingResponse>> Update(Guid id, UpdateListingRequest request, CancellationToken cancellationToken)
    {
        var command = new UpdateListingCommand(
            id, User.GetUserId(), request.Type, request.Price, request.Title, request.Description, request.ImageUrls ?? []);
        return await mediator.Send(command, cancellationToken);
    }

    [HttpPost("{id:guid}/submit")]
    [Authorize(Policy = Permissions.ListingsCreate)]
    public async Task<ActionResult<ListingResponse>> Submit(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new SubmitListingCommand(id, User.GetUserId()), cancellationToken);

    [HttpPost("{id:guid}/approve")]
    [Authorize(Policy = Permissions.ListingsApprove)]
    public async Task<ActionResult<ListingResponse>> Approve(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new ApproveListingCommand(id, User.GetUserId()), cancellationToken);

    [HttpPost("{id:guid}/reject")]
    [Authorize(Policy = Permissions.ListingsApprove)]
    public async Task<ActionResult<ListingResponse>> Reject(Guid id, RejectListingRequest request, CancellationToken cancellationToken) =>
        await mediator.Send(new RejectListingCommand(id, User.GetUserId(), request.Reason), cancellationToken);

    [HttpPost("{id:guid}/close")]
    [Authorize(Policy = Permissions.ListingsCreate)]
    public async Task<ActionResult<ListingResponse>> Close(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new CloseListingCommand(id, User.GetUserId(), CanReview()), cancellationToken);

    [HttpDelete("{id:guid}")]
    [Authorize(Policy = Permissions.ListingsCreate)]
    public async Task<IActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        await mediator.Send(new DeleteListingCommand(id, User.GetUserId()), cancellationToken);
        return NoContent();
    }

    private static PageOptions ToPaging(PagedRequest request) =>
        new(request.Page, request.PageSize, request.SortBy, request.Descending);

    private bool CanReview() => User.HasClaim(CustomClaimTypes.Permission, Permissions.ListingsApprove);
}
