using Bds.BuildingBlocks.Application.Exceptions;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Service.RealEstate.UseCases.Projects;

public static class ProjectRules
{
    public const string NotFoundMessage = "Không tìm thấy dự án.";

    public static void EnsureSuccess(ProjectWriteResult result)
    {
        switch (result)
        {
            case ProjectWriteResult.Success:
                return;
            case ProjectWriteResult.NotFound:
                throw AppException.NotFound(NotFoundMessage);
            case ProjectWriteResult.CodeExists:
                throw AppException.Conflict("Mã dự án đã tồn tại.");
            case ProjectWriteResult.DistrictNotInProvince:
                throw AppException.BusinessRule("Quận/huyện không thuộc tỉnh/thành đã chọn.");
            case ProjectWriteResult.HasProperties:
                throw AppException.BusinessRule("Không thể xóa dự án còn căn hộ.");
            default:
                throw new InvalidOperationException($"Unknown project write result: {result}.");
        }
    }
}
