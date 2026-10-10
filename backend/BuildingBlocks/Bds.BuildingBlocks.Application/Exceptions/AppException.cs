namespace Bds.BuildingBlocks.Application.Exceptions;

public sealed class AppException(ErrorType type, string message) : Exception(message)
{
    public ErrorType Type { get; } = type;

    public static AppException NotFound(string message) => new(ErrorType.NotFound, message);

    public static AppException Conflict(string message) => new(ErrorType.Conflict, message);

    public static AppException Unauthorized(string message) => new(ErrorType.Unauthorized, message);

    public static AppException Forbidden(string message) => new(ErrorType.Forbidden, message);

    public static AppException BusinessRule(string message) => new(ErrorType.BusinessRule, message);
}