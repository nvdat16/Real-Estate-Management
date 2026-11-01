using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Listings.Commands;
using Bds.Service.RealEstate.UseCases.Listings.Queries;

namespace Bds.Service.RealEstate.Interfaces;

public interface IListingService
{
    Task<ListingResponse> CreateAsync(CreateListingCommand command, CancellationToken cancellationToken);

    Task<ListingResponse> UpdateAsync(UpdateListingCommand command, CancellationToken cancellationToken);

    Task<ListingResponse> SubmitAsync(SubmitListingCommand command, CancellationToken cancellationToken);

    Task<ListingResponse> ApproveAsync(ApproveListingCommand command, CancellationToken cancellationToken);

    Task<ListingResponse> RejectAsync(RejectListingCommand command, CancellationToken cancellationToken);

    Task<ListingResponse> CloseAsync(CloseListingCommand command, CancellationToken cancellationToken);

    Task DeleteAsync(DeleteListingCommand command, CancellationToken cancellationToken);

    Task<ListingResponse> GetByIdAsync(GetListingByIdQuery query, CancellationToken cancellationToken);

    Task<PagedResult<ListingResponse>> SearchPublicAsync(SearchPublicListingsQuery query, CancellationToken cancellationToken);

    Task<PagedResult<ListingResponse>> SearchMineAsync(SearchMyListingsQuery query, CancellationToken cancellationToken);

    Task<PagedResult<ListingResponse>> SearchAsync(SearchListingsQuery query, CancellationToken cancellationToken);
}
