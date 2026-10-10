using System.Security.Claims;
using System.Text;
using Bds.BuildingBlocks.Application.Security;
using Bds.Domain.Identity.Entities;
using Bds.Service.Identity.Interfaces;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;

namespace Bds.Service.Identity.Helpers;

public sealed class JwtTokenGenerator(IOptions<JwtOptions> options) : IJwtTokenGenerator
{
    private readonly JsonWebTokenHandler _handler = new();

    public (string Token, DateTime ExpiresAt) Generate(User user)
    {
        var jwt = options.Value;
        var now = DateTime.UtcNow;
        var expiresAt = now.AddMinutes(jwt.AccessTokenMinutes);

        var claims = new List<Claim>
        {
            new(CustomClaimTypes.UserId, user.Id.ToString()),
            new(CustomClaimTypes.Email, user.Email),
            new(CustomClaimTypes.Name, user.FullName),
            new(CustomClaimTypes.Role, user.Role.Name),
        };

        claims.AddRange(user.Role.RolePermissions.Select(rp => 
            new Claim(CustomClaimTypes.Permission, rp.Permission.Code)));

        var descriptor = new SecurityTokenDescriptor
        {
            Issuer = jwt.Issuer,
            Audience = jwt.Audience,
            Subject = new ClaimsIdentity(claims),
            IssuedAt = now,
            NotBefore = now,
            Expires = expiresAt,
            SigningCredentials = new SigningCredentials(
                new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwt.SecretKey)),
                SecurityAlgorithms.HmacSha256),
        };

        return (_handler.CreateToken(descriptor), expiresAt);
    }
}