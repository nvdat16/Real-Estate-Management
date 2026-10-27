using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using FluentValidation;

namespace Bds.BuildingBlocks.Application.Validation;

public static class PagingValidationExtensions
{
    // Error keys stay "Page", "PageSize", "SortBy" so they match the query string parameters.
    public static void AddPagingRules<T>(this AbstractValidator<T> validator, params string[] sortFields)
        where T : IPagedQuery
    {
        validator.RuleFor(x => x.Paging.Page)
            .GreaterThanOrEqualTo(1)
            .OverridePropertyName("Page")
            .WithMessage("Trang phải từ 1 trở lên.");

        validator.RuleFor(x => x.Paging.PageSize)
            .InclusiveBetween(1, PageOptions.MaxPageSize)
            .OverridePropertyName("PageSize")
            .WithMessage($"Số dòng mỗi trang phải từ 1 đến {PageOptions.MaxPageSize}.");

        validator.RuleFor(x => x.Paging.SortBy)
            .Must(s => sortFields.Contains(s, StringComparer.OrdinalIgnoreCase))
            .When(x => x.Paging.SortBy is not null)
            .OverridePropertyName("SortBy")
            .WithMessage($"Chỉ sắp xếp được theo: {string.Join(", ", sortFields)}.");
    }
}
