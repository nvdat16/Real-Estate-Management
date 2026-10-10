using Bds.Domain.Identity.Entities;

namespace Bds.Service.Identity.Interfaces;

public interface IJwtTokenGenerator
{
    (string Token, DateTime ExpiresAt) Generate(User user);
}