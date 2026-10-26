using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Projects.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Projects.Validators;

public sealed class UpdateProjectValidator : AbstractValidator<UpdateProjectCommand>
{
    public UpdateProjectValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tên dự án không được để trống.")
            .MaximumLength(200).WithMessage("Tên dự án tối đa 200 ký tự.");

        RuleFor(x => x.ProvinceId).NotEmpty().WithMessage("Vui lòng chọn tỉnh/thành.");
        RuleFor(x => x.DistrictId).NotEmpty().WithMessage("Vui lòng chọn quận/huyện.");

        RuleFor(x => x.AddressLine)
            .NotEmpty().WithMessage("Địa chỉ không được để trống.")
            .MaximumLength(300).WithMessage("Địa chỉ tối đa 300 ký tự.");

        RuleFor(x => x.Developer)
            .NotEmpty().WithMessage("Chủ đầu tư không được để trống.")
            .MaximumLength(200).WithMessage("Chủ đầu tư tối đa 200 ký tự.");

        RuleFor(x => x.Status)
            .Must(EnumNames.IsDefinedName<ProjectStatus>)
            .WithMessage("Trạng thái phải là Active hoặc Inactive.");
    }
}
