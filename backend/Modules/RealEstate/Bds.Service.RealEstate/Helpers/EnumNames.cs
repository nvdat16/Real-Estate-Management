namespace Bds.Service.RealEstate.Helpers;

public static class EnumNames
{
    // Enum.TryParse also accepts "7" or "North,South", which would store an undefined value; only member names are allowed.
    public static bool IsDefinedName<TEnum>(string? value)
        where TEnum : struct, Enum =>
        value is not null && Enum.GetNames<TEnum>().Contains(value.Trim(), StringComparer.OrdinalIgnoreCase);
}
