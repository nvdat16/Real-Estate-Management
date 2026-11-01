using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Listings.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Listings.Validators;

public static class ListingContentValidationExtensions
{
    public const int MaxImages = 10;

    public static void AddListingContentRules<T>(this AbstractValidator<T> validator)
        where T : IListingContent
    {
        validator.RuleFor(x => x.Type)
            .Must(EnumNames.IsDefinedName<ListingType>)
            .WithMessage("Loại tin phải là Sale (bán) hoặc Rent (cho thuê).");

        validator.RuleFor(x => x.Price)
            .GreaterThan(0).WithMessage("Giá phải lớn hơn 0.")
            .LessThanOrEqualTo(100_000_000_000_000m).WithMessage("Giá tối đa 100.000 tỷ đồng.")
            .PrecisionScale(18, 0, ignoreTrailingZeros: true).WithMessage("Giá phải là số nguyên (VND).");

        validator.RuleFor(x => x.Title)
            .NotEmpty().WithMessage("Tiêu đề không được để trống.")
            .MaximumLength(200).WithMessage("Tiêu đề tối đa 200 ký tự.");

        validator.RuleFor(x => x.Description)
            .NotEmpty().WithMessage("Mô tả không được để trống.")
            .MaximumLength(5000).WithMessage("Mô tả tối đa 5000 ký tự.");

        validator.RuleFor(x => x.ImageUrls)
            .Must(urls => urls.Count <= MaxImages).WithMessage($"Tối đa {MaxImages} ảnh.");

        validator.RuleForEach(x => x.ImageUrls)
            .MaximumLength(500).WithMessage("Đường dẫn ảnh tối đa 500 ký tự.")
            .Must(BeHttpUrl).WithMessage("Đường dẫn ảnh phải là URL http hoặc https.");
    }

    private static bool BeHttpUrl(string url) =>
        Uri.TryCreate(url, UriKind.Absolute, out var uri) && (uri.Scheme == Uri.UriSchemeHttp || uri.Scheme == Uri.UriSchemeHttps);
}
