using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Projects.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Projects.Validators;

public sealed class SearchProjectsValidator : AbstractValidator<SearchProjectsQuery>
{
    private static readonly string[] SortFields = ["code", "name", "createdAt"];

    public SearchProjectsValidator()
    {
        RuleFor(x => x.Page).GreaterThanOrEqualTo(1).WithMessage("Trang phải từ 1 trở lên.");
        RuleFor(x => x.PageSize).InclusiveBetween(1, 100).WithMessage("Số dòng mỗi trang phải từ 1 đến 100.");

        RuleFor(x => x.Status)
            .Must(EnumNames.IsDefinedName<ProjectStatus>)
            .WithMessage("Trạng thái phải là Active hoặc Inactive.")
            .When(x => x.Status is not null);

        RuleFor(x => x.SortBy)
            .Must(s => SortFields.Contains(s, StringComparer.OrdinalIgnoreCase))
            .WithMessage("Chỉ sắp xếp được theo code, name hoặc createdAt.")
            .When(x => x.SortBy is not null);
    }
}
