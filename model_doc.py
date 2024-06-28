from shiny import ui

# MathJax script
mathjax_script = ui.markdown("""
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
""")


# Example Markdown content with LaTeX equations
Ts_and_Cs = r"""
        #### **Application Information**
                        
        ###### **Confidentiality and Usage Agreement**

        This software application, developed and maintained by <a href="https://www.gralix.co/" target="_blank">Gralix</a>, is a Python-Based solution expressly 
        designed to facilitate the computation of Expected Credit Losses (ECLs) in accordance with the specifications outlined by IFRS 9 and GPPC guidelines. 
        Gralix retains all rights to this application, extending its use to clients under stringent conditions aimed at maintaining the confidentiality of both the 
        application and its underlying codebase.

        ###### **1. Confidentiality Obligations:**

        By utilizing this application, the client agrees to uphold strict confidentiality regarding the application itself, its underlying computation engine, and 
        any derivative works. Under no circumstances shall the client distribute, share, or disseminate the application or its components to any third party without 
        prior written consent from Gralix.

        ###### **2. Authorized Usage:**

        The client may utilize the model outputs and accompanying documentation solely for internal purposes, limited to relevant staff members and key stakeholders 
        such as the Board of Directors and Auditors. Any sharing of outputs or documentation must adhere to the terms outlined in the contractual agreement between 
        the client and Gralix.

        ###### **3. Non-Disclosure and Non-Compete:**

        The client acknowledges and agrees that the proprietary nature of this application necessitates strict adherence to non-disclosure and non-compete obligations. 
        This includes refraining from reverse engineering, decompiling, or otherwise attempting to extract the underlying code or algorithms utilized within the 
        application.

        ###### **4. Legal Ramifications:**

        Violation of the confidentiality agreement outlined herein may result in legal action, including but not limited to injunctions, damages, and legal fees, 
        pursued by Gralix to protect its intellectual property rights.

        ###### **5. Acceptance of Terms:**

        By accessing or using this application, the client acknowledges and agrees to the terms and conditions set forth in this confidentiality and usage agreement. 
        Failure to comply with these terms may result in immediate termination of access to the application and potential legal consequences.

        ###### **6. Contact Information:**

        For inquiries regarding the terms of this agreement or to request permission for any use beyond its scope, please contact Gralix at
        [info@gralixconsulting.com](mailto:info@gralixconsulting.com).

        **<p style="color: red;">By proceeding to use this application, you affirm your understanding and acceptance of the terms outlined above.</p>**
                        
        """


equation = r'''I Hope works

$$\sqrt{\frac{\pi}{2}}$$'''

model_docs = r'''
#### **IFRS 9 Modelling Principles**

The GPPC summarizes the key modelling principles of IFRS 9 into 8 key components:
- ECL Methodology
- Definition of Default
- Probability of Default
- Loss Given Default
- Exposure at Default
- Discounting
- Staging Assessment
- Macroeconomic forecasts and forward-looking information

##### **1. Expected Credit Loss Methodology**

“IFRS 9 requires an entity to determine an expected credit loss (ECL) amount on a probability-weighted basis as the difference between the cash flows that are 
due to the entity in accordance with the contractual terms of a financial instrument and the cash flows that the entity expects to receive. Although IFRS 9 
establishes the objective, it generally does not prescribe particular methods or techniques for achieving it.” – GPPC 2.1.1.1

ECL measurements must be unbiased (i.e., neutral, not conservative and not biased towards optimism nor pessimism) and are determined by evaluating a range of 
possible outcomes. ECLs are generally measured based on the risk of default over one of two different time horizons, depending on whether the credit risk of the 
borrower has increased since initial recognition. The loss allowance for exposures that have not increased significantly in credit risk is based on 12-month ECLs. 
The loss allowance for exposures that have experienced a significant increase in credit risk is based on lifetime ECLs.

12-month ECLs are the portion of the lifetime ECLs that represent the ECLs that result from default events on a financial instrument that are possible within the 
12 months after the reporting date (or a shorter period if the expected life of the financial instrument is less than 12 months). Lifetime ECLs are the losses that 
result from all possible default events over the expected life of the financial instrument.

The ECL parameters (PD, LGD, EAD and effect of discounting) reflect the expected life or period of exposure. The entity may calculate each of these components for 
a series of time intervals over the period of exposure, i.e., monthly, quarterly, or annually, and sum them to derive the lifetime ECL.

**Collective Calculations and Segmentation**

ECLs on individually large exposures and credit-impaired loans are generally measured individually. For retail exposures and many exposures to small and medium-sized 
enterprises, where less borrower-specific information is available, ECLs are measured on a collective basis. This incorporates borrower specific information in 
combination with collective historical experiences and forward-looking information.

To assess the staging of exposures and to measure a loss allowance on a collective basis, the entity may group its exposures into segments based on shared credit 
risk characteristics. Examples of these characteristics include geographical region, type of customer, industry, product type, customer rating date of initial 
recognition, term to maturity, the quality of collateral and the loan to value ratio. The different segments reflect differences in PDs and in recovery rates in the 
event of default.

The entity may perform procedures to ensure that the groups of exposures continue to share credit characteristics, and to re-segment the portfolio, when necessary, 
considering changes in credit characteristics over time. These procedures should also guard against inappropriate reliance on models that may arise if re-segmentation 
is too frequent or granular and results in segments that are too narrow.

*NOTE: The standard prescribes two approaches for determining the ECL – the General Approach and the Simplified Approach. This application makes use of the general 
approach to determine the ECL – qualification criteria for the simplified approach can be found in paragraph 5.5.15 of the standard. Assets meeting these criteria 
have NOT been considered in this application.*


##### **2. Definition of Default**

The concept of “default” is crucial in the implementation of the IFRS 9 standard. IFRS 9 does not define the term “default” but instead requires an entity to do so. 
The definition should be consistent with the definition used fir internal credit risk management purposes and consider qualitative indicators when appropriate. While 
not exactly a definition for default, there is a rebuttable presumption within the standard that default takes place no later than 90 days past due however, no further 
guidance on how to define default is provided. The definition of default used affects the calculation of PDs, LGDs and EADs. Different definitions can lead to different 
ECL results.

*NOTE: The standard requires that when making the assessment of whether there has been a significant increase in credit risk (SICR) since initial recognition, an entity 
assesses the change in the risk of default occurring over the expected life of the financial instrument. For financial instruments that have not experienced SICR, ECLs 
are recognized in respect of default events that are possible within the next 12 months.*

##### **3. Probability of Default**

The probability of default can be used both as a parameter for determining the ECL and as an indicator for determining whether there has been a significant increase 
in credit risk. The PD used under IFRS 9 should be unbiased (should not include any conservatism or optimism) and should consider forward-looking information. 

As with the time horizons, two types of PDs are considered – 12-month PDs and Lifetime PDs. The 12-month PD is the estimated probability of default occurring within 
the next 12-months or over the remaining life of the financial instrument if it is less than 12 months. The lifetime PD is the estimated probability of default 
occurring over the remaining life of the financial instrument. PDs may be broken down further into marginal probabilities for the sub-periods within the remaining life.

There are various standard approaches to determining the PDs such as Generalized Linear Models (GLMs), Survival Modelling, Lifetime Machine Learning Modelling and 
Transition Matrix modelling. This application makes use of a transition matrix approach to determine the PDs. 

Historical periodic data is added to the connected database table – with schema calibrated to the model’s requirements. Alternatively, the data may be fed into the 
model in ‘.csv’ format. By default, the data required is the quarterly (or monthly, or annual) historical data showing the rating of each individual loan facility as 
at that point in time. This data is then used to determine the weighted average transition rates from one stage or rating grade to another – by default the model makes 
use of IFRS 9 staging (stage 1, stage 2 and stage 3) and creates transition matrices based on the weighted average transitions between these states. 

Once the transition rates have been determined, stage 3 is set as an absorbing state, i.e., transitions out of stage 3 are assumed to be impossible – See *Bellini; 
IFRS 9 and CECL Credit Risk Modelling and Validation*. The resulting matrix is taken as the base transition matrix or the 1-step transition matrix for the entity’s 
portfolio.

To determine the PD term-structure – the 12-month and lifetime PDs – the model uses the base transition matrix to compute the n-step transition matrices and obtain 
the cumulative PD curve. The marginal PDs follow from the properties of transition matrices as <insert equations>. The above is determined based on the facility 
segmentation per the provided dataset. By default, the model expects a segmentation column in the data and performs the above computations on a per segment basis. 
For example, in a portfolio with a mix of mortgage and asset financing loans, the above computations will be performed for mortgages and separately for asset financing. 




'''

pd_nav_text = r'''
        ###### **COMPUTED TERM STRUCTURE FOR PROBABILITIES OF DEFAULT BY LOAN SEGMENT:**

'''

base_matrix_text = r'''
        Below are the base transition matrices computed by the model. These are based on the historical quarterly transitions from one state to another 
        weighted by the outstanding loan balance. The default state is absorbing as it is assumed that transitions out of this state cannot occur. Transitions out 
        of default are modelled separately under cures. Cash recoveries from defaulted facilities are modelled under recoveries - see cure and recovery term structure 
        tabs.
'''


fli_nav_text = r'''
        ###### **Macroeconomic Data Sourced from the IMF World Economic Outlook Database**
        Please press the "Get Latest IMF Data" button to fetch the latest macroeconomic data from the IMF. For use in this application, this data has automatically been 
        converted to reflect the year-on-year percent change. The raw dataset can be found here: <a href="https://www.imf.org/external/datamapper/profile/ZMB" target="_blank">IMF DataMapper</a>

'''

lgd_note = r"""
        **<p style="color: red;">NOTE: Ensure Cure Rates and Recovery Rates are computed before proceeding!</p>**
"""