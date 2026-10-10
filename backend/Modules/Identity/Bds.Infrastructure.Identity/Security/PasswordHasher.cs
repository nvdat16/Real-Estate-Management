using Bds.Infrastructure.Identity.Interfaces;
using Microsoft.AspNetCore.Identity;

namespace Bds.Infrastructure.Identity.Security;

public sealed class PasswordHasher : IPasswordHasher
{
    private static readonly PasswordHasher<object> _hasher = new();

    public string Hash(string password) => _hasher.HashPassword(null!, password);

    public bool Verify(string passwordHash, string password) =>
        _hasher.VerifyHashedPassword(null!, passwordHash, password) != PasswordVerificationResult.Failed;
}