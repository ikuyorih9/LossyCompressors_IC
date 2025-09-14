# heatmap.py

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.colors import ListedColormap
import numpy.ma as ma

plt.rcParams['font.family'] = 'Times New Roman'

class HeatmapPlot:
    def __init__(
        self,
        title: str = "",
        title_size: int = 14,
        xlabel: str = None,
        xlabel_size: int = 12,
        ylabel: str = None,
        ylabel_size: int = 12,
        show_xlabel: bool = True,
        show_ylabel: bool = True,
        xlim=[],
        ylim=[],
        annot: bool = True,
        fmt: str = '.2f',
        cmap: str = 'viridis',
        figsize=(10, 8),
        cbar: bool = True,
        rotation_x: int = 45,
        rotation_y: int = 0,
        exceptions: list = None,             # <-- NOVO
        exception_color: str = "#9e9e9e",     # <-- NOVO
        annot_kws={"size": 14, "color": "black"}  # 👈 aqui você controla o tamanho/cor
    ):
        self.title = title
        self.title_size = title_size
        self.xlabel = xlabel
        self.xlabel_size = xlabel_size
        self.ylabel = ylabel
        self.ylabel_size = ylabel_size
        self.show_xlabel = show_xlabel
        self.show_ylabel = show_ylabel
        self.xlim = xlim
        self.ylim = ylim
        self.annot = annot
        self.fmt = fmt
        self.cmap = cmap
        self.figsize = figsize
        self.cbar = cbar
        self.rotation_x = rotation_x
        self.rotation_y = rotation_y
        self.exceptions = exceptions or []
        self.exception_color = exception_color
        self.annot_kws = annot_kws


    def generate(
        self,
        data: pd.DataFrame,
        index_col: str,
        columns_col: str,
        values_col: str,
        ax=None,
        output_image_path: str = None,
        title: str = None,
        show_plot: bool = True,
        vmin: float = None,  # ✅ adicione isso
        vmax: float = None ,  # ✅ e isso
        
    ):
        """
        Gera um heatmap a partir do DataFrame formatado.
        """

        pivoted = data.pivot(index=index_col, columns=columns_col, values=values_col)
        # Máscara robusta para exceções
        mask = pivoted.applymap(lambda x: x in self.exceptions)


        valores_validos = pivoted[~mask]
        vmin = vmin if vmin is not None else valores_validos.min().min()
        vmax = vmax if vmax is not None else valores_validos.max().max()

        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        sns.heatmap(
            pivoted,
            mask=mask,
            annot=self.annot,
            fmt=self.fmt,
            cmap=self.cmap,
            ax=ax,
            cbar=self.cbar,
            vmin=vmin,
            vmax=vmax,
            linewidths=0.5,
            linecolor='white',
            annot_kws=self.annot_kws
        )
        exception_data = pivoted.copy()
        exception_mask = ~pivoted.applymap(lambda x: x in self.exceptions)
        masked_exception_data = ma.masked_where(exception_mask, exception_data)

        ax.pcolor(
            masked_exception_data,
            cmap=ListedColormap([self.exception_color]),
            edgecolors='white',
            linewidths=0.5
        )

        ax.set_title(title or self.title, pad=20, fontsize=self.title_size)

        # Eixo X
        if self.show_xlabel:
            ax.set_xlabel(self.xlabel or columns_col, fontsize=self.xlabel_size)
        else:
            ax.set_xlabel("")
            ax.set_xticklabels([])
            
        # Eixo Y
        if self.show_ylabel:
            ax.set_ylabel(self.ylabel or index_col, fontsize=self.ylabel_size)
        else:
            ax.set_ylabel("")
            ax.set_yticklabels([])

        # ax.set_xlabel(self.xlabel or columns_col, fontsize=self.xlabel_size)
        # ax.set_ylabel(self.ylabel or index_col, fontsize=self.ylabel_size)

        # Rotaciona os rótulos
        ax.set_xticklabels(ax.get_xticklabels(), rotation=self.rotation_x)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=self.rotation_y)

        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")
        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax

    def generate_binary(
        self,
        data: pd.DataFrame,
        index_col: str,
        columns_col: str,
        values_col: str,
        condition,
        colors: list = ["#d73027", "#1a9850"],  # [False, True]
        nan_color: str = "#9e9e9e",             # cinza para NaN
        ax=None,
        output_image_path: str = None,
        title: str = None,
        show_plot: bool = True,
    ):
        """
        Gera um heatmap binário com cores para True/False e cinza para NaN.
        Pode exibir anotação em notação científica (sci_notation).
        """
        pivoted = data.pivot(index=index_col, columns=columns_col, values=values_col)

        # Avalia condição
        if callable(condition):
            cond_matrix = pivoted.applymap(lambda x: condition(x) if pd.notnull(x) else np.nan)
        elif isinstance(condition, str):
            cond_matrix = pivoted.applymap(lambda x: eval(f"x {condition}") if pd.notnull(x) else np.nan)
        else:
            raise ValueError("condition deve ser função lambda ou string, e.g. '> 0.05'")

        # Mapeia: -1 = NaN, 0 = False, 1 = True
        cat_matrix = cond_matrix.copy()
        cat_matrix = cat_matrix.where(~cat_matrix.isna(), -1)
        cat_matrix = cat_matrix.where(cat_matrix != False, 0)
        cat_matrix = cat_matrix.where(cat_matrix != True, 1)
        cat_matrix = cat_matrix.astype(int)

        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        # Cores: índices → [-1, 0, 1] → cinza, vermelho, verde
        cmap_bin = ListedColormap([nan_color, colors[0], colors[1]])
        plot_data = cat_matrix.replace({-1: 0, 0: 1, 1: 2})  # shift para 0,1,2

        # ----- Formatação dos valores -----
        annot_values = pivoted.copy()
        # annot_values = annot_values.where(~annot_values.isna(), "")  # NaN → ""
        # Heatmap
        heatmap = sns.heatmap(
            plot_data,
            cmap=cmap_bin,
            cbar=False,
            fmt = self.fmt ,
            annot=annot_values if self.annot else False, 
            linewidths=0.5,
            linecolor="white",
            ax=ax
        )

        for text_obj, val in zip(heatmap.texts, pivoted.to_numpy().ravel()):
            if pd.isna(val):
                text_obj.set_text("")

        ax.set_title(title or self.title, pad=20, fontsize=self.title_size)
        ax.set_xlabel(self.xlabel or columns_col, fontsize=self.xlabel_size)
        ax.set_ylabel(self.ylabel or index_col, fontsize=self.ylabel_size)

        ax.set_xticklabels(ax.get_xticklabels(), rotation=self.rotation_x)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=self.rotation_y)

        if output_image_path:
            fig.savefig(output_image_path, bbox_inches="tight")
            print(f"Imagem salva em: {output_image_path}")

        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax



    def generate_multiplots(
        self,
        plot_functions: list,
        output_image_path: str = None,
        title: str = None,
        nrows: int = 1,
        ncols: int = None
    ):
        """
        Executa uma lista de funções de plotagem (plot_functions), cada uma desenhando em um Axes.
        """

        num = len(plot_functions)
        if ncols is None:
            ncols = num
        if nrows * ncols < num:
            raise ValueError("nrows * ncols deve ser >= número de plots")

        fig = plt.figure(figsize=(self.figsize[0] * ncols, self.figsize[1] * nrows))
        gs = fig.add_gridspec(nrows, ncols)

        axs = []
        i = 0
        while i < num:
            # ⬇️ Se este for o último plot e sobrar espaço (ex: 3 gráficos num 2x2)
            if i == num-1 and (num % ncols) == 1 and ncols > 1:
                row = i // ncols
                ax = fig.add_subplot(gs[row, :])  # ocupa TODAS as colunas da linha
            else:
                row = i // ncols
                col = i % ncols
                ax = fig.add_subplot(gs[row, col])
            axs.append(ax)
            i += 1

        # roda cada função de plot no eixo correspondente
        for ax, plot_fn in zip(axs, plot_functions):
            plot_fn(ax)

        fig.suptitle(self.title if not title else title, fontsize=self.title_size)
        plt.tight_layout()
        plt.subplots_adjust(top=0.85)  # Se precisar de mais espaço para title
        plt.subplots_adjust(wspace=0.3)  # aumento do gap horizontal entre os subplots (padrão = 0.2)


        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")

        plt.show()

if __name__ == "__main__":
    # Carrega dados de teste
    df = pd.read_csv("../../results/13_python2_tests/damicore_time_stats.csv", sep='\t', decimal=',')

    df = df[df['load'] == 'ALL-COMPRESSORS_SERIAL']
    df = df[['load', 'type', 'compressor', 'median_time', 'median_process_time']]

    print(df)

    # Exemplo simples: comparação entre compressor x tipo
    heat = HeatmapPlot(
        title="Heatmap de Tempo Mediano",
        xlabel="Tipo",
        ylabel="Compressor",
        cmap="YlGnBu",
        fmt=".2f"
    )

    heat.generate(
        data=df,
        index_col="compressor",
        columns_col="type",
        values_col="median_time"
    )

    # Vários heatmaps com multiplots
    df_melted = df.melt(
        id_vars=["compressor", "type"],
        value_vars=["median_time", "median_process_time"],
        var_name="metric",
        value_name="value"
    )

    metrics = df_melted["metric"].unique()

    print(df_melted)

    def make_plot(metric_name):
        def plot(ax):
            filtered = df_melted[df_melted["metric"] == metric_name]
            heat.generate(
                data=filtered,
                index_col="compressor",
                columns_col="type",
                values_col="value",
                ax=ax,
                show_plot=False,
                title=f"Heatmap - {metric_name}"
            )
        return plot

    heat.generate_multiplots(
        plot_functions=[make_plot(m) for m in metrics],
        title="Multiplos Heatmaps",
        nrows=1,
        ncols=2
    )
