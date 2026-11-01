using Bds.BuildingBlocks.Application.Exceptions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.UseCases.Listings;
using Bds.Service.RealEstate.UseCases.Listings.Commands;
using Bds.Service.RealEstate.UseCases.Listings.Queries;

namespace Bds.Service.RealEstate.Services;

public sealed class ListingService(IListingRepository listingRepository) : IListingService
{
    public async Task<ListingResponse> CreateAsync(CreateListingCommand command, CancellationToken cancellationToken)
    {
        var id = Guid.CreateVersion7();
        var result = await listingRepository.CreateAsync(
            id,
            command.UserId,
            command.PropertyId,
            ParseType(command.Type),
            command.Price,
            command.Title.Trim(),
            command.Description.Trim(),
            TrimUrls(command.ImageUrls),
            cancellationToken);
        ListingRules.EnsureSuccess(result);

        return await LoadAsync(id, cancellationToken);
    }

    public async Task<ListingResponse> UpdateAsync(UpdateListingCommand command, CancellationToken cancellationToken)
    {
        var result = await listingRepository.UpdateAsync(
            command.Id,
            command.UserId,
            ParseType(command.Type),
            command.Price,
            command.Title.Trim(),
            command.Description.Trim(),
            TrimUrls(command.ImageUrls),
            cancellationToken);
        ListingRules.EnsureSuccess(result);

        return await LoadAsync(command.Id, cancellationToken);
    }

    public async Task<ListingResponse> SubmitAsync(SubmitListingCommand command, CancellationToken cancellationToken)
    {
        ListingRules.EnsureSuccess(await listingRepository.SubmitAsync(command.Id, command.UserId, cancellationToken));
        return await LoadAsync(command.Id, cancellationToken);
    }

    public async Task<ListingResponse> ApproveAsync(ApproveListingCommand command, CancellationToken cancellationToken)
    {
        ListingRules.EnsureSuccess(await listingRepository.ApproveAsync(command.Id, command.ReviewerId, cancellationToken));
        return await LoadAsync(command.Id, cancellationToken);
    }

    public async Task<ListingResponse> RejectAsync(RejectListingCommand command, CancellationToken cancellationToken)
    {
        var result = await listingRepository.RejectAsync(command.Id, command.ReviewerId, command.Reason.Trim(), cancellationToken);
        ListingRules.EnsureSuccess(result);
        return await LoadAsync(command.Id, cancellationToken);
    }

    public async Task<ListingResponse> CloseAsync(CloseListingCommand command, CancellationToken cancellationToken)
    {
        var result = await listingRepository.CloseAsync(command.Id, command.UserId, command.CanCloseAny, cancellationToken);
        ListingRules.EnsureSuccess(result);
        return await LoadAsync(command.Id, cancellationToken);
    }

    public async Task DeleteAsync(DeleteListingCommand command, CancellationToken cancellationToken)
    {
        ListingRules.EnsureSuccess(await listingRepository.DeleteAsync(command.Id, command.UserId, cancellationToken));
    }

    public async Task<ListingResponse> GetByIdAsync(GetListingByIdQuery query, CancellationToken cancellationToken)
    {
        var listing = await listingRepository.GetByIdAsync(query.Id, cancellationToken);
        if (listing is null || !ListingRules.CanView(listing, query.CurrentUserId, query.CanViewAll))
        {
            throw AppException.NotFound(ListingRules.NotFoundMessage);
        }

        return ListingMapping.ToResponse(listing);
    }

    public Task<PagedResult<ListingResponse>> SearchPublicAsync(SearchPublicListingsQuery query, CancellationToken cancellationToken)
    {
        var filter = new ListingFilter(
            PublicOnly: true,
            AgentUserId: null,
            Status: null,
            query.Keyword,
            query.Type is null ? null : ParseType(query.Type),
            query.MinPrice,
            query.MaxPrice,
            query.ProvinceId,
            query.DistrictId,
            query.ProjectId,
            query.MinArea,
            query.MaxArea,
            query.Bedrooms,
            query.Paging);
        return SearchAsync(filter, cancellationToken);
    }

    public Task<PagedResult<ListingResponse>> SearchMineAsync(SearchMyListingsQuery query, CancellationToken cancellationToken) =>
        SearchAsync(BackOfficeFilter(query.UserId, query.Keyword, query.Status, query.Type, query.Paging), cancellationToken);

    public Task<PagedResult<ListingResponse>> SearchAsync(SearchListingsQuery query, CancellationToken cancellationToken) =>
        SearchAsync(BackOfficeFilter(null, query.Keyword, query.Status, query.Type, query.Paging), cancellationToken);

    private async Task<PagedResult<ListingResponse>> SearchAsync(ListingFilter filter, CancellationToken cancellationToken)
    {
        var (items, totalCount) = await listingRepository.SearchAsync(filter, cancellationToken);
        return new PagedResult<ListingResponse>(
            items.Select(ListingMapping.ToResponse).ToList(), filter.Paging.Page, filter.Paging.PageSize, totalCount);
    }

    private static ListingFilter BackOfficeFilter(Guid? agentUserId, string? keyword, string? status, string? type, PageOptions paging) =>
        new(
            PublicOnly: false,
            agentUserId,
            status is null ? null : Enum.Parse<ListingStatus>(status, ignoreCase: true),
            keyword,
            type is null ? null : ParseType(type),
            MinPrice: null,
            MaxPrice: null,
            ProvinceId: null,
            DistrictId: null,
            ProjectId: null,
            MinArea: null,
            MaxArea: null,
            Bedrooms: null,
            paging);

    // The caller just changed this listing, so it is always allowed to see the result.
    private async Task<ListingResponse> LoadAsync(Guid id, CancellationToken cancellationToken)
    {
        var listing = await listingRepository.GetByIdAsync(id, cancellationToken)
            ?? throw AppException.NotFound(ListingRules.NotFoundMessage);
        return ListingMapping.ToResponse(listing);
    }

    private static ListingType ParseType(string type) => Enum.Parse<ListingType>(type, ignoreCase: true);

    private static string[] TrimUrls(IReadOnlyList<string> urls) => urls.Select(u => u.Trim()).ToArray();
}
