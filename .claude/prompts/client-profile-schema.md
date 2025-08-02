# Client Profile Schema - Wealth Management CRM

## SOURCE DOCUMENTATION
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| mt_transcript   | meeting transcript file name                 | str       | meeting_01_investment_strategies.vtt|

## CLIENT IDENTIFICATION & KYC
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| first_name      | client's first name                          | str       | Sarah                               |
| last_name       | client's last name                           | str       | Thompson                            |
| age             | client's age                                 | int       | 45                                  |
| gender          | client's gender (M/F/NB)                     | str       | F                                   |
| citizenship     | client's citizenship                         | str       | US_citizen                          |
| residency       | country of tax residency                     | str       | USA                                 |
| state_province  | state/province of residence                  | str       | California                          |

## HOUSEHOLD & DEMOGRAPHICS
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| household_num   | number of families inside client's household | int       | 2                                   |
| new_immigrant   | new immigrant status                         | str       | n                                   |
| occupation      | client's primary occupation                  | str       | Software_Engineer                   |

## ACCOUNT HOLDINGS WITH OUR INSTITUTION
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| tenure          | client's tenure with our institution (years) | int       | 5                                   |
| t_bal           | client's transactional account balance       | float     | 35000.00                            |
| i_bal_reg       | invest-acc balance in tax shelter            | float     | 200000.00                           |
| i_bal_non_reg   | invest-acc balance in non-tax shelter        | float     | 650000.00                           |
| b_bal           | client's borrowing account balance           | float     | 425000.00                           |
| c_bal           | client's credit account balance              | float     | 12500.00                            |

## EXTERNAL ASSETS & TOTAL WEALTH
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| ext_asset_value | client's asset value outside our institution | float     | 650000.00                           |

## INVESTMENT INDICATORS & PREFERENCES
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| crossborder_ind | client using crossborder service or not      | str       | n                                   |
| donation_ind    | client donates or not                        | str       | y                                   |
| re_ind          | client invests in real-estate or not         | str       | y                                   |

## TAX & COMPLIANCE
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| tax_complexity  | tax complications rating: 1(easy) - 5(hard)  | int       | 3                                   |

## RISK PROFILE & INVESTMENT OBJECTIVES
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| risk_tolerance  | risk tolerance level (1-10)                  | int       | 6                                   |
| risk_capacity   | financial capacity for risk (1-10)           | int       | 7                                   |
| investment_exp  | years of investment experience               | int       | 10                                  |
| primary_goal    | primary investment objective                 | str       | retirement_planning                 |
| time_horizon    | investment time horizon (years)              | int       | 15                                  |

## INCOME & CASH FLOW
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| annual_income   | total annual income                          | float     | 225000.00                           |
| income_stability| income stability (stable/variable/seasonal)  | str       | stable                              |
| savings_rate    | monthly savings capacity                     | float     | 8500.00                             |
| liquidity_needs | liquidity requirement level (low/med/high)   | str       | medium                              |

## INVESTMENT PREFERENCES
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| investment_style| conservative/moderate/aggressive             | str       | moderate                            |
| asset_alloc_pref| preferred stock/bond allocation (e.g. 60/40) | str       | 70/30                               |
| sector_pref     | preferred sectors (comma-separated)          | str       | tech,healthcare,energy              |
| esg_interest    | ESG investing interest (y/n)                 | str       | y                                   |

## WEALTH PLANNING NEEDS
| Column Name     | Column Description                           | Data Type | Example Value                       |
| -------------   | ---------------------------------------------|-----------|-------------------------------------|
| retirement_age  | target retirement age                        | int       | 65                                  |
| estate_planning | estate planning needs (y/n)                  | str       | y                                   |
| education_fund  | education funding needed (y/n)               | str       | y                                   |
| insurance_review| insurance review needed (y/n)                | str       | n                                   |

