using Bds.BuildingBlocks.Application.Validation;
using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Properties.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Properties.Validators;

public sealed class SearchPropertiesValidator : AbstractValidator<SearchPropertiesQuery>
{
    public SearchPropertiesValidator()
    {
        this.AddPagingRules("code", "area", "floor", "createdAt");

        RuleFor(x => x.Status)
            .Must(EnumNames.IsDefinedName<PropertyStatus>)
            .WithMessage("Trạng thái phải là Available, Reserved, Sold hoặc Rented.")
            .When(x => x.Status is not null);

        RuleFor(x => x.Direction)
            .Must(EnumNames.IsDefinedName<Direction>)
            .WithMessage("Hướng không hợp lệ.")
            .When(x => x.Direction is not null);

        RuleFor(x => x.MinArea).GreaterThanOrEqualTo(0).WithMessage("Diện tích tối thiểu không được âm.");
        RuleFor(x => x.MaxArea)
            .GreaterThanOrEqualTo(x => x.MinArea).WithMessage("Diện tích tối đa phải lớn hơn hoặc bằng diện tích tối thiểu.")
            .When(x => x.MinArea is not null && x.MaxArea is not null);

        RuleFor(x => x.Bedrooms).InclusiveBetween(0, 20).WithMessage("Số phòng ngủ phải từ 0 đến 20.");
    }
}
