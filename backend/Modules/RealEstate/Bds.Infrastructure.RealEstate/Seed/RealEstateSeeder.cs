using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.Contexts;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.RealEstate.Seed;

public static class RealEstateSeeder
{
    // Sample data only: three cities with a few districts each, using the pre-2025 administrative codes.
    private static readonly (string Code, string Name, (string Code, string Name)[] Districts)[] Locations =
    [
        ("01", "Hà Nội",
        [
            ("001", "Ba Đình"), ("002", "Hoàn Kiếm"), ("005", "Cầu Giấy"),
            ("006", "Đống Đa"), ("007", "Hai Bà Trưng"), ("019", "Nam Từ Liêm"),
        ]),
        ("79", "TP. Hồ Chí Minh",
        [
            ("760", "Quận 1"), ("770", "Quận 3"), ("778", "Quận 7"),
            ("765", "Bình Thạnh"), ("769", "Thủ Đức"),
        ]),
        ("48", "Đà Nẵng",
        [
            ("491", "Thanh Khê"), ("492", "Hải Châu"), ("493", "Sơn Trà"), ("494", "Ngũ Hành Sơn"),
        ]),
    ];

    // Safe to run on every deployment: only inserts locations that do not exist yet.
    public static async Task SeedAsync(RealEstateContext context, CancellationToken cancellationToken = default)
    {
        var provinces = await context.Provinces.ToDictionaryAsync(p => p.Code, cancellationToken);
        var districtCodes = (await context.Districts.Select(d => d.Code).ToListAsync(cancellationToken)).ToHashSet();

        foreach (var (code, name, districts) in Locations)
        {
            if (!provinces.TryGetValue(code, out var province))
            {
                province = Province.Create(code, name);
                context.Provinces.Add(province);
            }

            foreach (var (districtCode, districtName) in districts.Where(d => !districtCodes.Contains(d.Code)))
            {
                context.Districts.Add(District.Create(province.Id, districtCode, districtName));
            }
        }

        await context.SaveChangesAsync(cancellationToken);
    }
}
