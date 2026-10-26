using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Properties.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Properties.Validators;

public sealed class CreatePropertyValidator : AbstractValidator<CreatePropertyCommand>
{
    public CreatePropertyValidator()
    {
        RuleFor(x => x.ProjectId).NotEmpty().WithMessage("Vui lòng chọn dự án.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Mã căn hộ không được để trống.")
            .MaximumLength(50).WithMessage("Mã căn hộ tối đa 50 ký tự.")
            .Matches("^[A-Za-z0-9-]+$").WithMessage("Mã căn hộ chỉ gồm chữ, số và dấu gạch ngang.");

        RuleFor(x => x.Area)
            .GreaterThan(0).WithMessage("Diện tích phải lớn hơn 0.")
            .LessThanOrEqualTo(100_000).WithMessage("Diện tích tối đa 100.000 m².")
            .PrecisionScale(10, 2, ignoreTrailingZeros: true).WithMessage("Diện tích tối đa 2 chữ số thập phân.");

        RuleFor(x => x.Floor).InclusiveBetween(-10, 200).WithMessage("Tầng phải từ -10 đến 200.");

        RuleFor(x => x.Position)
            .NotEmpty().WithMessage("Vị trí không được để trống.")
            .MaximumLength(100).WithMessage("Vị trí tối đa 100 ký tự.");

        RuleFor(x => x.Bedrooms).InclusiveBetween(0, 20).WithMessage("Số phòng ngủ phải từ 0 đến 20.");

        RuleFor(x => x.Direction)
            .Must(EnumNames.IsDefinedName<Direction>)
            .WithMessage("Hướng phải là một trong: North, South, East, West, NorthEast, NorthWest, SouthEast, SouthWest.");
    }
}
