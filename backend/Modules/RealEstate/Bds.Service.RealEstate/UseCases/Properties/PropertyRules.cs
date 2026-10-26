using Bds.BuildingBlocks.Application.Exceptions;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Service.RealEstate.UseCases.Properties;

public static class PropertyRules
{
    public const string NotFoundMessage = "Không tìm thấy căn hộ.";

    public static void EnsureSuccess(PropertyWriteResult result)
    {
        switch (result)
        {
            case PropertyWriteResult.Success:
                return;
            case PropertyWriteResult.NotFound:
                throw AppException.NotFound(NotFoundMessage);
            case PropertyWriteResult.CodeExists:
                throw AppException.Conflict("Mã căn hộ đã tồn tại trong dự án.");
            case PropertyWriteResult.ProjectInactive:
                throw AppException.BusinessRule("Dự án đang ngừng hoạt động, không thể thêm căn hộ.");
            case PropertyWriteResult.ProjectNotFound:
                throw AppException.NotFound("Không tìm thấy dự án.");
            case PropertyWriteResult.NotAvailable:
                throw AppException.BusinessRule("Chỉ xóa được căn hộ đang còn trống.");
            default:
                throw new InvalidOperationException($"Unknown property write result: {result}.");
        }
    }
}
