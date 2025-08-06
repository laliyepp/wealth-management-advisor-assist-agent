"""Client profile database for in-memory storage and retrieval."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ClientProfile:
    """Client profile data structure."""
    mt_transcript: str
    first_name: str
    last_name: str
    age: int
    gender: str
    citizenship: str
    residency: str
    state_province: Optional[str]
    household_num: int
    new_immigrant: str
    occupation: str
    tenure: int
    t_bal: Optional[float]
    i_bal_reg: Optional[float]
    i_bal_non_reg: Optional[float]
    b_bal: Optional[float]
    c_bal: Optional[float]
    ext_asset_value: Optional[float]
    crossborder_ind: str
    donation_ind: Optional[str]
    re_ind: str
    tax_complexity: int
    risk_tolerance: int
    risk_capacity: int
    investment_exp: int
    primary_goal: str
    time_horizon: int
    annual_income: float
    income_stability: str
    savings_rate: Optional[float]
    liquidity_needs: str
    investment_style: str
    asset_alloc_pref: str
    sector_pref: Optional[str]
    esg_interest: Optional[str]
    retirement_age: int
    estate_planning: Optional[str]
    education_fund: str
    insurance_review: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientProfile":
        """Create ClientProfile from dictionary."""
        return cls(**data)

    @property
    def full_name(self) -> str:
        """Get full client name."""
        return f"{self.first_name} {self.last_name}"


class ClientProfileDB:
    """In-memory database for client profiles."""

    def __init__(self):
        self.profiles: Dict[str, ClientProfile] = {}
        self._loaded = False

    def load_from_jsonl(self, file_path: str) -> None:
        """Load client profiles from JSONL file."""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Client profile file not found: {file_path}")
                return

            self.profiles.clear()
            
            with path.open('r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        profile = ClientProfile.from_dict(data)
                        
                        # Use full name as key (case-insensitive)
                        key = profile.full_name.lower()
                        self.profiles[key] = profile
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num}: {e}")
                    except TypeError as e:
                        logger.warning(f"Invalid profile data on line {line_num}: {e}")
            
            self._loaded = True
            logger.info(f"Loaded {len(self.profiles)} client profiles from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading client profiles: {e}")

    def get_profile_by_first_name(self, client_first_name: str) -> Optional[ClientProfile]:
        """
        Extract client profile information using a given client first name.
        
        Args:
            client_first_name: First name or partial name of the client (case-insensitive)
            
        Returns:
            ClientProfile if found, None otherwise
        """
        if not self._loaded:
            logger.warning("Client profiles not loaded. Call load_from_jsonl() first.")
            return None
        
        # Normalize the search name
        search_name = client_first_name.strip().lower()
        
        # Direct match first
        if search_name in self.profiles:
            return self.profiles[search_name]
        
        # Partial match - find first profile where name contains the search term
        for name, profile in self.profiles.items():
            if search_name in name:
                return profile
        
        # Try matching first name only
        for name, profile in self.profiles.items():
            if profile.first_name.lower() == search_name:
                return profile
        
        # Try matching last name only
        for name, profile in self.profiles.items():
            if profile.last_name.lower() == search_name:
                return profile
        
        return None

    def get_all_profiles(self) -> List[ClientProfile]:
        """Get all loaded client profiles."""
        return list(self.profiles.values())

    def get_profile_names(self) -> List[str]:
        """Get list of all client names."""
        return [profile.full_name for profile in self.profiles.values()]

    def is_loaded(self) -> bool:
        """Check if profiles have been loaded."""
        return self._loaded

    def count(self) -> int:
        """Get number of loaded profiles."""
        return len(self.profiles)


# Global instance
client_db = ClientProfileDB()


def get_client_profile(client_first_name: str) -> Optional[Dict[str, Any]]:
    """
    Tool function to extract client profile information using a given client name.
    
    Args:
        client_first_name: The name of the client to search for
        
    Returns:
        Dictionary containing client profile data if found, None otherwise
    """
    profile = client_db.get_profile_by_first_name(client_first_name)
    if profile:
        # Convert to dictionary for JSON serialization
        return {
            'client_name': profile.full_name,
            'age': profile.age,
            'gender': profile.gender,
            'citizenship': profile.citizenship,
            'residency': profile.residency,
            'state_province': profile.state_province,
            'occupation': profile.occupation,
            'annual_income': profile.annual_income,
            'investment_balances': {
                'total_balance': profile.t_bal,
                'registered_investments': profile.i_bal_reg,
                'non_registered_investments': profile.i_bal_non_reg,
                'bank_balance': profile.b_bal,
                'cash_balance': profile.c_bal,
                'external_assets': profile.ext_asset_value
            },
            'risk_profile': {
                'risk_tolerance': profile.risk_tolerance,
                'risk_capacity': profile.risk_capacity,
                'investment_experience': profile.investment_exp
            },
            'financial_goals': {
                'primary_goal': profile.primary_goal,
                'time_horizon': profile.time_horizon,
                'retirement_age': profile.retirement_age
            },
            'preferences': {
                'investment_style': profile.investment_style,
                'asset_allocation': profile.asset_alloc_pref,
                'sector_preference': profile.sector_pref,
                'esg_interest': profile.esg_interest
            },
            'planning_needs': {
                'estate_planning': profile.estate_planning,
                'education_fund': profile.education_fund,
                'insurance_review': profile.insurance_review
            },
            'tax_complexity': profile.tax_complexity,
            'savings_rate': profile.savings_rate,
            'liquidity_needs': profile.liquidity_needs,
            'meeting_transcript': profile.mt_transcript
        }
    return None