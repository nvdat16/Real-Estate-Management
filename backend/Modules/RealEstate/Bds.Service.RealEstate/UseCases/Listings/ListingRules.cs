using Bds.BuildingBlocks.Application.Exceptions;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Service.RealEstate.UseCases.Listings;

public static class ListingRules
{
    public const string NotFoundMessage = "Không tìm thấy tin đăng.";

    public static void EnsureSuccess(ListingWriteResult result)
    {
        switch (result)
        {
            case ListingWriteResult.Success:
                return;
            case ListingWriteResult.NotFound:
                throw AppException.NotFound(NotFoundMessage);
            case ListingWriteResult.NotOwner:
                throw AppException.Forbidden("Bạn không có quyền thao tác trên tin đăng này.");
            case ListingWriteResult.InvalidStatus:
                throw AppException.BusinessRule("Trạng thái hiện tại của tin đăng không cho phép thao tác này.");
            case ListingWriteResult.AgentProfileRequired:
                throw AppException.BusinessRule("Bạn cần cập nhật hồ sơ môi giới trước khi đăng tin.");
            case ListingWriteResult.PropertyNotFound:
                throw AppException.NotFound("Không tìm thấy căn hộ.");
            case ListingWriteResult.PropertyNotAvailable:
                throw AppException.BusinessRule("Căn hộ không còn trống.");
            case ListingWriteResult.PropertyHasActiveListing:
                throw AppException.Conflict("Căn hộ đã có tin đang chờ duyệt hoặc đã duyệt.");
            default:
                throw new InvalidOperationException($"Unknown listing write result: {result}.");
        }
    }

    // Non-public listings are hidden (404, not 403) from everyone except their agent and reviewers.
    public static bool CanView(ListingReadModel listing, Guid? currentUserId, bool canViewAll) =>
        listing.IsPublic || canViewAll || listing.AgentUserId == currentUserId;
}
