using Bds.BuildingBlocks.Application.Validation;
using Bds.Service.RealEstate.UseCases.Agents.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Agents.Validators;

public sealed class SearchAgentsValidator : AbstractValidator<SearchAgentsQuery>
{
    public SearchAgentsValidator()
    {
        this.AddPagingRules("fullName", "createdAt");
    }
}
