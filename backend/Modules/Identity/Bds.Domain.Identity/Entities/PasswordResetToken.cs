using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.Identity.Entities;
public sealed class PasswordResetToken : BaseEntity
{
    private PasswordResetToken(){}

    public Guid UserId { get; private set; }
    public string TokenHash { get; private set; } = null!;
    public DateTime ExpiresAt { get; private set; }
    public DateTime? UsedAt { get; private set; }

    public static PasswordResetToken Create(Guid userId, string tokenHash, DateTime expiresAt)
    {
        return new PasswordResetToken
        {
            UserId = userId,
            TokenHash = tokenHash,
            ExpiresAt = expiresAt,
            CreatedAt = DateTime.UtcNow,
        };
    }

    public bool IsValid(DateTime now) => UsedAt is null && now < ExpiresAt;

    public void MarkUsed(DateTime now)
    {
           UpdatedAt = now;
        UsedAt = now;
    }
}
