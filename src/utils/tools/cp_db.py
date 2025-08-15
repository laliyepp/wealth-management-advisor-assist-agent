"""Client profile database for in-memory storage and retrieval."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ClientProfile:
    """Client profile data structure focused on client-specific information.
    
    Contains client personal info, financial situation, preferences, and planning needs
    while excluding internal account/system specific data.
    """
    # SOURCE DOCUMENTATION
    mt_transcript: str  # meeting transcript file name
    
    # CLIENT IDENTIFICATION & KYC
    first_name: str  # client's first name
    last_name: str  # client's last name
    age: int  # client's age
    gender: str  # client's gender (M/F/NB)
    citizenship: str  # client's citizenship
    residency: str  # country of tax residency
    state_province: Optional[str]  # state/province of residence
    occupation: str  # client's primary occupation
    
    # HOUSEHOLD INFO
    household_num: int  # number of families inside client's household
    new_immigrant: str  # new immigrant status
    
    # CLIENT WEALTH & EXTERNAL ASSETS
    ext_asset_value: Optional[float]  # client's asset value outside our institution
    annual_income: float  # total annual income
    income_stability: str  # income stability (stable/variable/seasonal)
    savings_rate: Optional[float]  # monthly savings capacity
    
    # CLIENT PREFERENCES & BEHAVIOR
    donation_ind: Optional[str]  # client donates or not
    re_ind: str  # client invests in real-estate or not
    crossborder_ind: str  # client using crossborder service or not
    
    # TAX SITUATION
    tax_complexity: int  # tax complications rating: 1(easy) - 5(hard)
    
    # RISK PROFILE & INVESTMENT OBJECTIVES
    risk_tolerance: int  # risk tolerance level (1-10)
    risk_capacity: int  # financial capacity for risk (1-10)
    investment_exp: int  # years of investment experience
    primary_goal: str  # primary investment objective
    time_horizon: int  # investment time horizon (years)
    liquidity_needs: str  # liquidity requirement level (low/med/high)
    
    # INVESTMENT PREFERENCES
    investment_style: str  # conservative/moderate/aggressive
    asset_alloc_pref: str  # preferred stock/bond allocation (e.g. 60/40)
    sector_pref: Optional[str]  # preferred sectors (comma-separated)
    esg_interest: Optional[str]  # ESG investing interest (y/n)
    
    # WEALTH PLANNING NEEDS
    retirement_age: int  # target retirement age
    estate_planning: Optional[str]  # estate planning needs (y/n)
    education_fund: str  # education funding needed (y/n)
    insurance_review: Optional[str]  # insurance review needed (y/n)
    
    # ACCOUNT RELATIONSHIP (minimal institutional data)
    tenure: int  # client's tenure with our institution (years)
    t_bal: Optional[float]  # client's transactional account balance
    i_bal_reg: Optional[float]  # invest-acc balance in tax shelter
    i_bal_non_reg: Optional[float]  # invest-acc balance in non-tax shelter
    b_bal: Optional[float]  # client's borrowing account balance
    c_bal: Optional[float]  # client's credit account balance

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
        Dictionary containing client profile data focused on client-specific information, None otherwise
    """
    profile = client_db.get_profile_by_first_name(client_first_name)
    if profile:
        # Convert to client-focused dictionary
        return {
            'client_identification': {
                'full_name': profile.full_name,
                'age': profile.age,
                'gender': profile.gender,
                'citizenship': profile.citizenship,
                'residency': profile.residency,
                'state_province': profile.state_province,
                'occupation': profile.occupation
            },
            'household_info': {
                'household_size': profile.household_num,
                'new_immigrant_status': profile.new_immigrant
            },
            'financial_situation': {
                'annual_income': profile.annual_income,
                'income_stability': profile.income_stability,
                'monthly_savings_rate': profile.savings_rate,
                'external_asset_value': profile.ext_asset_value,
                'tax_complexity_rating': profile.tax_complexity
            },
            'investment_profile': {
                'risk_tolerance': profile.risk_tolerance,
                'risk_capacity': profile.risk_capacity,
                'investment_experience_years': profile.investment_exp,
                'primary_goal': profile.primary_goal,
                'time_horizon_years': profile.time_horizon,
                'liquidity_needs': profile.liquidity_needs
            },
            'investment_preferences': {
                'investment_style': profile.investment_style,
                'asset_allocation_preference': profile.asset_alloc_pref,
                'sector_preferences': profile.sector_pref,
                'esg_interest': profile.esg_interest
            },
            'client_behavior': {
                'donation_activity': profile.donation_ind,
                'real_estate_investing': profile.re_ind,
                'crossborder_services': profile.crossborder_ind
            },
            'planning_needs': {
                'target_retirement_age': profile.retirement_age,
                'estate_planning_needed': profile.estate_planning,
                'education_fund_needed': profile.education_fund,
                'insurance_review_needed': profile.insurance_review
            },
            'account_summary': {
                'relationship_tenure_years': profile.tenure,
                'account_balances': {
                    'transactional': profile.t_bal,
                    'registered_investments': profile.i_bal_reg,
                    'non_registered_investments': profile.i_bal_non_reg,
                    'borrowing': profile.b_bal,
                    'credit': profile.c_bal
                }
            }
        }
    return None