import openpyxl.writer
from shiny import App, render, ui, reactive, req
from faicons import icon_svg
import io
import shinyswatch
import pandas as pd
import numpy as np
from functools import partial
from ecl_module import LossGivenDefault, create_ead_instance, ECL_Calc, sum_of_ecl, plot_ecl_bar, plot_ecl_pie, plot_bar_loan_type, plot_pie_loan_type, merge_original_balance
from db_app_funtions import connect_fli
from macro_module import fetch_imf
from data_validation import data_prep, recoveries_prep, merge_recoveries, add_dates, staging_map
from matrix_functions import base_matrices, absorbing_state, extract_pds, cure_rate, multi_to_single, plot_rates_px
from model_doc import mathjax_script, Ts_and_Cs, model_docs, base_matrix_text, fli_nav_text
from shinywidgets import render_plotly, output_widget, render_plotly
from shiny.types import FileInfo
from pandarallel import pandarallel
import openpyxl
import csv

pandarallel.initialize()


MAT_SIZE = 3
MAT_MULT = 121
staging_map_partial = partial(staging_map, matrix_size = MAT_SIZE)

app_ui = ui.page_fluid(shinyswatch.theme.cosmo(),
    ui.page_navbar(
        ui.nav_panel(
            "Ts & Cs", 
            ui.column(
                12, 
                ui.div(
                    ui.column(
                        8, 
                        [mathjax_script, 
                         ui.div(
                            ui.markdown(Ts_and_Cs), 
                            style="text-align: justify;")], 
                        offset=2),
                    style="text-align: justify; overflow-y: scroll; overflow-x: scroll" ), offset=0), 
                    icon=icon_svg("gavel")), 
        

        ui.nav_panel(
            "Documentation", 
            ui.column(
                12,
                ui.div(
                    ui.column(
                        8,
                        [ui.div(
                            ui.markdown(model_docs),
                            style="text-align: justify;")],
                        offset=2
                    ),
                    style="text-align: justify; overflow-y: scroll; overflow-x: scroll"
                )
            ),
            icon=icon_svg("book")
            ),

        ui.nav_panel(
            "Probability of Default",
            ui.row(
                ui.column(
                    2,
                    [ui.card(ui.input_date("val_date", ui.markdown("""###### **Valuation Date:**"""), value="2024-03-31", format="dd-mm-yyyy"),
                     ui.input_file('upload_pd',ui.markdown("""###### **UPLOAD PD FILE**"""), accept=[".csv"], width="200px")),
                     ui.card(ui.markdown("""###### **If Recovery Data is Available:**"""),
                     ui.input_file("upload_recoveries", ui.markdown("""###### **UPLOAD RECOVERIES FILE**"""), accept=[".csv"], width="200px")),
                     ui.input_task_button("compute_pds","Compute PDs", width="200px", icon=icon_svg("database")),]
                    ),
                ui.column(
                    10,
                    ui.navset_card_tab(
                        ui.nav_panel(
                            "Stage 1 Marginal", 
                            [ui.markdown("###### **STAGE 1 MARGINAL PD TERM STRUCTURE BY SEGMENT:**"), 
                             ui.output_data_frame("s1_marg")]
                        ),
                        ui.nav_panel(
                            "Stage 2 Marginal",
                            [ui.markdown("###### **STAGE 2 MARGINAL PD TERM STRUCTURE BY SEGMENT:**"),
                             ui.output_data_frame("s2_marg")]
                        ),
                        ui.nav_panel(
                            "Stage 1 Cumulative",
                            [ui.markdown("###### **STAGE 1 CUMULATIVE PD TERM STRUCTURE BY SEGMENT:**"),
                             ui.output_data_frame("s1_cml")]
                        ),
                        ui.nav_panel(
                            "Stage 2 Cumulative",
                            [ui.markdown("###### **STAGE 2 CUMULATIVE PD TERM STRUCTURE BY SEGMENT:**"), 
                             ui.output_data_frame('s2_cml')]
                        ),
                        ui.nav_panel(
                            "Base Matrices",
                            [ui.markdown(base_matrix_text), 
                             ui.output_data_frame('pd_mats')]
                        ),
                        ui.nav_panel(
                            "Marginal PD Plots",
                            [ui.markdown("###### **Graphs of Stage 1 and Stage 2 Marginal Probabilities of Default:**"), 
                             ui.row(ui.card(output_widget("pd_plot"))),
                             ui.row(ui.card(output_widget("pd_plot2")))
                             ]
                        ),
                        ui.nav_panel(
                            "Cumulative PD Plots",
                            [ui.markdown("###### **Graphs of Stage 1 and Stage 2 Cumulative Probabilities of Default:**"), 
                             ui.row(ui.card(output_widget("pd_plot3"))),
                             ui.row(ui.card(output_widget("pd_plot4")))]
                        ),                                                
                    ),
                    offset=0
                )
                ),
                icon=icon_svg('percent')
        ),

        ui.nav_panel(
            "Exposure at Default",
            ui.row(
                ui.column(
                    2,
                    [ui.input_file("upload_exposures", ui.markdown("###### **UPLOAD LOAN BOOK:**"), accept=[".csv"], width="200px"),
                     ui.markdown("""###### **Or**"""),
                     ui.input_task_button("db_loanbook", "Calculate EAD", icon=icon_svg("database"), width="200px"),]
                ),
                ui.column(
                    10,
                    ui.navset_card_tab(
                        ui.nav_panel(
                            "Current Loan Book",
                            [ui.markdown("###### **LOAN BOOK AS AT THE VALUATION DATE:**"),
                             ui.output_data_frame("loanbook")]
                        ),
                        ui.nav_panel(
                            "EAD Term Structure",
                            ui.layout_columns(
                                ui.card(
                                    [ui.markdown("###### **SELECT A LOAN TO VIEW EAD TERM STRUCTURE:**"),
                                     ui.output_data_frame("loan_selector")]
                                ),
                                ui.card(
                                    [ui.markdown("###### **EAD TERM STRUCTURE:**"),
                                     ui.output_data_frame('ead_term')]
                                )
                            )
                        )
                    )
                )
            )
            

        ,icon=icon_svg("coins")    
        ),

        ui.nav_panel(
            "Loss Given Default",
            ui.row(
                ui.column(
                    12,
                    ui.navset_card_tab(
                        ui.nav_panel(
                            "Cure Rate Term Structure",
                            ui.layout_columns(
                                ui.card(
                                    [ui.markdown("###### **CURE RATE TERM STRUCTURE BY SEGMENT**"),
                                     ui.output_data_frame("cure_rates_df")]
                                )
                            ) 
                        ),
                        ui.nav_panel(
                            "Recovery Rate Term Structure",
                            ui.layout_columns(
                                ui.card(
                                    [ui.markdown("###### **RECOVERY RATE TERM STRUCTURE BY SEGMENT**"),
                                     ui.output_data_frame("recovery_rates")]
                                )
                            )  
                        ),
                        ui.nav_panel(
                            "LGD Term Structure",
                            ui.layout_columns(
                                ui.column(
                                    2,
                                    [ui.input_task_button("lgd_compute", "Calculate LGD", icon=icon_svg("calculator"), width="200px"),
                                     ]
                                ),
                                ui.card(
                                    [ui.markdown("###### **ALL LOANS:** Select a Loan to view the LGD Term Structure"),
                                     ui.output_data_frame("lgd_selector")]
                                ),
                                ui.card(
                                    [ui.markdown("###### **LGD TERM STRUCTURE**"),
                                     ui.output_data_frame("lgd_term")]
                                ),
                                col_widths={'sm': (2,7,3)}
                            )
                        )
                    ), 
                )
            )

        ,icon=icon_svg("money-bill-transfer")
        ),

        ui.nav_panel(
            "Forward-Looking Information",
            ui.row(
                ui.column(
                    2,
                    [ui.input_task_button("get_data", "Get Latest IMF Data")]
                ),

                ui.column(
                    9,
                    ui.navset_card_tab(
                        ui.nav_panel(
                            "IMF Macro Data",
                            [ui.markdown(fli_nav_text),
                             ui.output_data_frame("imf_data")]
                        ),
                        ui.nav_panel(
                            "FLI-Adjustment Factors",
                            ui.layout_columns(
                                
                                ui.card(
                                    [ui.input_task_button("get_fli", "Compute FLI-Adjustments")]
                                ),
                                ui.card(
                                    [ui.output_data_frame("fli_data")]
                                ),
                                col_widths=[2, 9]
                            )
                            
                        )
                    ),
                    offset=0
                ),
            ),

        icon=icon_svg("magnifying-glass-chart")    
        ),

        ui.nav_panel(
            "Expected Credit Loss",
            ui.row(
                ui.column(
                    2,
                    ui.layout_column_wrap(
                        ui.input_task_button("ecl_compute", "Calculate ECL", icon=icon_svg("calculator"), width="200px"),
                        ui.download_button("download_ecl_xlsx", "Download Excel", icon=icon_svg("download"), width="200px"),
                        ui.download_button("download_ecl_csv", "Download CSV", icon=icon_svg("download"), width="200px")

                    ),
                ),
                ui.column(
                    10,
                    ui.navset_card_tab(
                        ui.nav_panel(
                            "ECL Summary",
                            ui.row(ui.card(
                                [
                                ui.markdown("###### **ECL PER STAGE**"),
                                ui.layout_columns(
                                    ui.card(
                                        ui.value_box(
                                            title="TOTAL ECL:",
                                            value=ui.output_ui("total_ecl"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-cyan-yellow",
                                            width="50px"
                                            )),
                                    ui.card(
                                        ui.value_box(
                                            title="STAGE 1 ECL",
                                            value=ui.output_ui("total_stage1"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-blue-green"
                                            )),
                                    ui.card(
                                        ui.value_box(
                                            title="STAGE 2 ECL",
                                            value=ui.output_ui("total_stage2"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-green-yellow"
                                            )),
                                    ui.card(
                                        ui.value_box(
                                            title="STAGE 3 ECL",
                                            value=ui.output_ui("total_stage3"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-orange-red"
                                            )),
                                )
                                ]
                                )),
                            ui.row(ui.card(
                                [
                                ui.markdown("###### **EAD PER STAGE**"),
                                ui.layout_columns(
                                    ui.card(
                                        ui.value_box(
                                            title="TOTAL EXPOSURE:",
                                            value=ui.output_ui("total_ead"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-cyan-yellow",
                                            width="50px"
                                            )),
                                    ui.card(
                                        ui.value_box(
                                            title="STAGE 1 EXPOSURE",
                                            value=ui.output_ui("total_stage1_ead"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-blue-green"
                                            )),
                                    ui.card(
                                        ui.value_box(
                                            title="STAGE 2 EXPOSURE",
                                            value=ui.output_ui("total_stage2_ead"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-green-yellow"
                                            )),
                                    ui.card(
                                        ui.value_box(
                                            title="STAGE 3 EXPOSURE",
                                            value=ui.output_ui("total_stage3_ead"),
                                            showcase=icon_svg("money-bill"),
                                            theme="bg-gradient-orange-red"
                                            )),
                                )
                                ]
                                )),
                            ui.row(ui.card(
                                output_widget(
                                    "ecl_plot_bar"
                                ),
                                max_height='400.px'
                            )),
                            ui.row(ui.card(
                               output_widget(
                                   "ecl_plot_pie"
                               ),
                               max_height='400.px'
                            )),
                            ui.row(ui.card(
                                output_widget(
                                    "loan_type_bar"
                                ),
                                max_height='400.px'
                            )),
                            ui.row(ui.card(
                               output_widget(
                                   "loan_type_pie"
                               ),
                               max_height='400.px'
                            ))
                        ),
                        ui.nav_panel(
                            "Term Structure Per Loan",
                            ui.layout_columns(
                                ui.card(
                                    [ui.markdown("###### **SELECT AN ACCOUNT TO VIEW THE SPECIFIC ECL TERM STRUCTURE**"),
                                     ui.output_data_frame("ecl_table")]
                                ),
                                ui.card(
                                    [ui.markdown("###### **ECL TERM STRUCTURE**"),
                                     ui.output_data_frame("ecl_single")]
                                ),
                                col_widths=[8,4]
                            )
                        ),                        
                    ), 
                )
            ),

        icon=icon_svg("calculator")    
        )


        ,title="IFRS 9 Engine", fillable=True, id="page"
         
))


def server(input, output, session):

    stage_1_marg = reactive.value(None)
    stage_2_marg = reactive.value(None)
    stage_1_cml = reactive.value(None)
    stage_2_cml = reactive.value(None)
    base_mat = reactive.value(None)
    cures = reactive.value(None)
    recoveries = reactive.value(None)
    LOANBOOK = reactive.value(None)
    EAD = reactive.value(None)
    LGD = reactive.value(None)
    ECL_df = reactive.value(None)
    # LOANTYPE_df = reactive.value(None)
    # ECL Summary Values
    ECL = reactive.value(None)
    ECL_TOTAL = reactive.Value(0)
    ECL_STAGE1 = reactive.value(0)
    ECL_STAGE2 = reactive.value(0)
    ECL_STAGE3 = reactive.value(0)
    # EAD Summary Values
    EAD_TOTAL = reactive.Value(0)
    EAD_STAGE1 = reactive.value(0)
    EAD_STAGE2 = reactive.value(0)
    EAD_STAGE3 = reactive.value(0)
    valuation_date = reactive.value(None)
    # GRAPH_DF = reactive.value(None)
    # loan_df = reactive.value(None)

    # @render.ui
    # def theme():
    #     return shinyswatch.theme.cosmo()
    
    @reactive.calc
    def parsed_pd_file():
        file: list[FileInfo] | None = input.upload_pd()
        if file is None:
            return pd.DataFrame()
        
        return pd.read_csv( # pyright: ignore[reportUnknownMemberType]
            file[0]['datapath']
            ) 

    @reactive.effect
    @reactive.event(input.upload_pd)
    def _():
        notif = ui.notification_show("PD File Upload Complete!", duration=5, close_button=True)


    @reactive.calc
    def parsed_recoveries_file():
        file: list[FileInfo] | None = input.upload_recoveries()
        if file is None:
            return pd.DataFrame()
        
        return pd.read_csv( # pyright: ignore[reportUnknownMemberType]
            file[0]['datapath']
            ) 

    @reactive.effect
    @reactive.event(input.upload_recoveries)
    def _():
        notif = ui.notification_show("Recoveries File Upload Complete!", duration=5, close_button=True)


    @reactive.Effect
    def _():
        nonlocal valuation_date
        valuation_date = pd.to_datetime(input.val_date())


    @render.data_frame
    @reactive.event(input.compute_pds)
    def s1_marg():

        with ui.Progress(1, 10) as p:
            p.set(message="Reading file contents...", detail="Computing PD Term Structure from Uploaded Data")

            pd_data = parsed_pd_file()
            recoveries_data = parsed_recoveries_file()

            nonlocal base_mat, cures, recoveries

            if not pd_data.empty and not recoveries_data.empty:
                pd_df, period = data_prep(pd_data, MAT_SIZE, valuation_date)
                recoveries_df = recoveries_prep(recoveries_data)[0]
                merged_data = merge_recoveries(pd_df, recoveries_df, valuation_date)
                matrices = absorbing_state(base_matrices(merged_data), period=period)
                # absorbing_state(matrices, MAT_SIZE, period=period)
                cr_rr = cure_rate(merged_data, MAT_MULT, period=period)

                base_mat = multi_to_single(matrices)
                cures = add_dates(cr_rr[0], valuation_date)
                recoveries = add_dates(cr_rr[1], valuation_date)

                del pd_df, recoveries_df, merged_data, cr_rr

            elif not pd_data.empty:
                pd_df, period = data_prep(pd_data, MAT_SIZE, valuation_date)
                matrices = absorbing_state(base_matrices(pd_df), period=period)
                # absorbing_state(matrices, MAT_SIZE)
                cr_rr = cure_rate(pd_df, MAT_MULT, period=period)

                base_mat = multi_to_single(matrices)
                cures = add_dates(cr_rr[0], valuation_date)
                recoveries = add_dates(cr_rr[1], valuation_date)

                del pd_df, cr_rr

            else:
                ui.notification_show("PD File is required!", duration=5, close_button=True)
                return pd.DataFrame()

            final_output = extract_pds(matrices, 3, MAT_MULT)

            nonlocal stage_1_marg, stage_2_marg, stage_1_cml, stage_2_cml #, loan_df
            stage_1_marg = add_dates(final_output[0], valuation_date)
            stage_2_marg = add_dates(final_output[1], valuation_date)
            stage_1_cml = add_dates(final_output[2], valuation_date)
            stage_2_cml = add_dates(final_output[3], valuation_date)
            # loan_df = all_data[2]
            del matrices, final_output

        ui.modal_show(ui.modal(f"PDs Computed Successfully", title=f"Operation Complete", easy_close=True))

        return render.DataGrid(stage_1_marg, filters=True)
    

    @render.data_frame
    @reactive.event(input.compute_pds)
    def s2_marg():
        return render.DataGrid(stage_2_marg, filters=True)
    
    @render.data_frame
    @reactive.event(input.compute_pds)
    def s1_cml():
        return render.DataGrid(stage_1_cml, filters=True)

    @render.data_frame
    @reactive.event(input.compute_pds)
    def s2_cml():
        return render.DataGrid(stage_2_cml, filters=True)
    
    @render.data_frame
    @reactive.event(input.compute_pds)
    def pd_mats():
        return render.DataGrid(base_mat, filters=True)

    @render_plotly
    @reactive.event(input.compute_pds)
    def pd_plot():
        # if not isinstance(stage_1_marg, pd.DataFrame):
        #     return None
        # elif isinstance(stage_1_marg, pd.DataFrame):
        df = stage_1_marg.drop("DATE", axis=1)
        graph = plot_rates_px(df, "Stage 1 Marginal Probability of Default", x_range=12)

        return graph

    @render_plotly
    @reactive.event(input.compute_pds)
    def pd_plot2():
        # if not isinstance(stage_2_marg, pd.DataFrame):
        #     return None
        # elif isinstance(stage_2_marg, pd.DataFrame):
        df = stage_2_marg.drop("DATE", axis=1)
        graph = plot_rates_px(df, "Stage 2 Marginal Probability of Default", x_range=12)

        return graph
    
    @render_plotly
    @reactive.event(input.compute_pds)
    def pd_plot3():
        # if not isinstance(stage_1_cml, pd.DataFrame):
        #     return None
        # elif isinstance(stage_1_cml, pd.DataFrame):
        df = stage_1_cml.drop("DATE", axis=1)
        graph = plot_rates_px(df, "Stage 1 Cumulative Probability of Default", x_range=12)

        return graph

    @render_plotly
    @reactive.event(input.compute_pds)
    def pd_plot4():
        # if not isinstance(stage_2_cml, pd.DataFrame):
        #     return None
        # elif isinstance(stage_2_cml, pd.DataFrame):
        df = stage_2_cml.drop("DATE", axis=1)
        graph = plot_rates_px(df, "Stage 2 Cumulative Probability of Default", x_range=12)

        return graph

    @reactive.calc
    def parsed_ead_file():
        file: list[FileInfo] | None = input.upload_exposures()
        if file is None:
            return pd.DataFrame()
        
        return pd.read_csv( # pyright: ignore[reportUnknownMemberType]
            file[0]['datapath']
            ) 
        
    @reactive.effect
    @reactive.event(input.upload_exposures)
    def _():
        notif = ui.notification_show("File Upload Complete!", duration=2, close_button=True)

    
    @render.data_frame
    # @render.effect
    @reactive.event(input.db_loanbook)
    def loanbook():
        nonlocal LOANBOOK, EAD
        with ui.Progress(1, 10) as p:
            p.set(message="Reading file content...", detail="Computing EAD Term Structure for Loan Book as at valuation Date")
            LOANBOOK = parsed_ead_file()
            
            LOANBOOK['staging'] = LOANBOOK['days_past_due'].map(staging_map_partial)

            EAD = pd.DataFrame({"EAD OBJECTS": LOANBOOK.parallel_apply(create_ead_instance, axis=1)}) # create a loan instance 

        ui.modal_show(ui.modal(f"EAD Computed Successfully", title="Operation Complete", easy_close=True))

        return render.DataGrid(LOANBOOK, filters=True)

    @render.data_frame
    @reactive.event(input.db_loanbook)
    def loan_selector():
        # if not isinstance(LOANBOOK, pd.DataFrame):
        #     return None
        # Subset the Dataframe to display only the listed columns
        return render.DataGrid(LOANBOOK[['account_no', 'client_id', 'disbursement_date', 'maturity_date', 'loan_type', 'staging']],
                            #    height="500px", 
                               filters=True, 
                               row_selection_mode='single')
    
    @reactive.calc
    def amort():
        selected_row = req(input.loan_selector_selected_rows())
        # selected_row = input.loan_selector_selected_rows()

        selected_loan = list(selected_row)[0]
        df = EAD["EAD OBJECTS"][selected_loan].amortization
        df['Expected Date'] = df['Expected Date'].dt.strftime('%d-%m-%Y')

        return df
    
    @render.data_frame
    def ead_term():

        return render.DataGrid(
            amort(),
            # height="500px",
            filters=True,
            row_selection_mode='single'
        )
    
    @render.data_frame
    @reactive.event(input.compute_pds)
    def cure_rates_df():
        return render.DataGrid(cures, filters=True, height="500px")
    
    @render.data_frame
    @reactive.event(input.compute_pds)
    def recovery_rates():
        if not isinstance(recoveries, pd.DataFrame):
            return None
        else:
            return render.DataGrid(recoveries, filters=True, height="500px")
    

    @render.data_frame
    @reactive.event(input.lgd_compute)
    def lgd_selector():
        with ui.Progress(1, 10) as p:
            p.set(message="Loading EAD Term Structure...", detail="Computing LGD Term Structure from EAD Term Structure")
            nonlocal LGD, LOANBOOK

            if not isinstance(cures, pd.DataFrame):
                return None
            
            elif isinstance(recoveries, pd.DataFrame):
                def create_lgd_instance(row):
                    return LossGivenDefault(
                        exposure=row['EAD OBJECTS'],
                        cure_rate=cures,
                        recovery_rate=recoveries
                    )
                LGD = pd.DataFrame({"LGD OBJECTS": EAD.parallel_apply(create_lgd_instance, axis=1)})

            else:
                def create_lgd_instance(row):
                    return LossGivenDefault(
                        exposure=row['EAD OBJECTS'],
                        cure_rate=cures,
                    )
                LGD = pd.DataFrame({"LGD OBJECTS": EAD.parallel_apply(create_lgd_instance, axis=1)})

        ui.modal_show(ui.modal(f"LGD Computed Successfully", title="Operation Complete", easy_close=True))

        return render.DataGrid(LOANBOOK[['account_no', 'client_id', 'disbursement_date', 'maturity_date', 'loan_type', 'staging']],
                            #    height="500px", 
                               filters=True, 
                               row_selection_mode='single')
        
    
    @reactive.calc
    def lgd_amort():
        rows = req(input.lgd_selector_selected_rows())

        selected_loan = list(rows)[0]
        df = LGD["LGD OBJECTS"][selected_loan].lgd_schedule
        df['Expected Date'] = df['Expected Date'].dt.strftime('%d-%m-%Y')
        return df        

    @render.data_frame
    def lgd_term():

        return render.DataGrid(
            lgd_amort(),
            # height="500px",
            filters=True,
            row_selection_mode='single'
        )

    @render.data_frame
    @reactive.event(input.get_data)
    async def imf_data():
        macro_data = await fetch_imf()
        return render.DataGrid(macro_data, filters=True)

    @render.data_frame
    @reactive.event(input.get_fli)
    def fli_data():
        fli_adjustments = connect_fli()
        return render.DataGrid(fli_adjustments, filters=True)
    
    @render.text
    @reactive.event(input.ecl_compute)
    def total_ecl():
        with ui.Progress(1, 10) as p:
            p.set(message="Loading PD, EAD and LGD Models...", detail="Computing ECL as at the Valuation Date")
            nonlocal ECL_df, ECL, ECL_TOTAL, ECL_STAGE1, ECL_STAGE2, ECL_STAGE3, EAD_TOTAL, EAD_STAGE1, EAD_STAGE2, EAD_STAGE3, LOANBOOK
            ECL_df = ECL_Calc(EAD, LGD, stage_1_marg, stage_2_marg)
            ECL_dff = sum_of_ecl(ECL_df)

            ECL = merge_original_balance(LOANBOOK, ECL_dff)

            del ECL_dff

            ECL[['Exposure', 'ECL']] = ECL[['Exposure', 'ECL']].round(2)
            ECL_TOTAL = float(ECL["ECL"].sum())
            ECL_STAGE1 = ECL.groupby("Stage")["ECL"].sum().loc["stage_1"]
            ECL_STAGE2 = ECL.groupby("Stage")["ECL"].sum().loc["stage_2"]
            ECL_STAGE3 = ECL.groupby("Stage")["ECL"].sum().loc["stage_3"]

            EAD_TOTAL = ECL['Exposure'].sum()
            EAD_STAGE1 = ECL.groupby("Stage")["Exposure"].sum().loc["stage_1"]
            EAD_STAGE2 = ECL.groupby("Stage")["Exposure"].sum().loc["stage_2"]
            EAD_STAGE3 = ECL.groupby("Stage")["Exposure"].sum().loc["stage_3"]           

        ui.modal_show(ui.modal(f"ECL Computed Successfully", title="Operation Complete", easy_close=True))

        return f"{ECL_TOTAL:,.0f}"
    
    # ECL Summary Values Displayed
    @render.text
    @reactive.event(input.ecl_compute)
    def total_stage1():
        return f"{ECL_STAGE1:,.0f}"
    
    @render.text
    @reactive.event(input.ecl_compute)
    def total_stage2():
        return f"{ECL_STAGE2:,.0f}"
    
    @render.text
    @reactive.event(input.ecl_compute)
    def total_stage3():
        return f"{ECL_STAGE3:,.0f}"
    
    # EAD Summary Values Displayed
    @render.text
    @reactive.event(input.ecl_compute)
    def total_ead():
        return f"{EAD_TOTAL:,.0f}"

    @render.text
    @reactive.event(input.ecl_compute)
    def total_stage1_ead():
        return f"{EAD_STAGE1:,.0f}"
    
    @render.text
    @reactive.event(input.ecl_compute)
    def total_stage2_ead():
        return f"{EAD_STAGE2:,.0f}"
    
    @render.text
    @reactive.event(input.ecl_compute)
    def total_stage3_ead():
        return f"{EAD_STAGE3:,.0f}"
    
    @render_plotly
    @reactive.event(input.ecl_compute)
    def ecl_plot_bar():
        graph = plot_ecl_bar(ECL)
        return graph
    
    @render_plotly
    @reactive.event(input.ecl_compute)
    def ecl_plot_pie():
        graph = plot_ecl_pie(ECL)
        return graph
    
    @render_plotly
    @reactive.event(input.ecl_compute)
    def loan_type_bar():
        graph = plot_bar_loan_type(ECL)
        return graph
    
    @render_plotly
    @reactive.event(input.ecl_compute)
    def loan_type_pie():
        graph = plot_pie_loan_type(ECL)
        return graph


    @render.data_frame
    @reactive.event(input.ecl_compute)
    def ecl_table():
        
        return render.DataGrid(ECL, filters=True, row_selection_mode='single')
    

    @reactive.calc
    def ecl_term():
        row = req(input.ecl_table_selected_rows())

        selected_row = list(row)[0]

        selected_account = ECL["Account Number"][selected_row]
        df = ECL_df[ECL_df["Account Number"] == selected_account]
        return df[["ECL", "PD", "LGD", "EAD", "Loan Type"]]
    
    @render.data_frame
    def ecl_single():
        return render.DataGrid(
            ecl_term(),
            # height="500px",
            filters=True,
            row_selection_mode='single'
        )
    
    # @output
    # @ui.output_ui
    # @reactive.event
    # def download_button_ui():
    #     return ui.download_button('download_ecl', 'ECL Output')

    @render.download(
        filename=lambda: f"Expected Credit Loss - Output as at {valuation_date.strftime('%Y-%m-%d')}.xlsx"
    )
    def download_ecl_xlsx():

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            ECL.to_excel(writer, index=False, sheet_name=f"{valuation_date.strftime('%d-%m-%Y')}")
        
        output.seek(0)
        return output
    
    
    @render.download(
        filename=lambda: f"Expected Credit Loss - Output as at {valuation_date.strftime('%Y-%m-%d')}.csv"
    )
    def download_ecl_csv():
        output = io.BytesIO()
        ECL.to_csv(output, index=False)
        output.seek(0)
        return output
    
app = App(app_ui, server)
