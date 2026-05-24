from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.proposal import (
    ProposalCreate, ProposalRead, ProposalUpdate,
    ProposalProductCreate, ProposalSchemeCreate,
    ApprovalCreate, ApprovalRead
)

__all__ = [
    "ClientCreate", "ClientRead", "ClientUpdate",
    "ProposalCreate", "ProposalRead", "ProposalUpdate",
    "ProposalProductCreate", "ProposalSchemeCreate",
    "ApprovalCreate", "ApprovalRead",
]
