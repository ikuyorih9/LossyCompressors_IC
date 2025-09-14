# boxplot.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Define a fonte global como Times New Roman
plt.rcParams['font.family'] = 'Times New Roman'

class BoxplotPlot:
    def __init__(
        self,
        title: str = "",
        title_size: int = 14,
        xlabel: str = None,
        xlabel_size: int = 12,
        ylabel: str = None,
        ylabel_size: int = 12,
        figsize=(12, 8),
        rotation_x: int = 45,
        rotation_y: int = 0,
        palette: str = "Set2",
        showfliers: bool = True,
        box_width: float = 0.6,
        ticklabel_size: int = 12
    ):
        self.title = title
        self.title_size = title_size
        self.xlabel = xlabel
        self.xlabel_size = xlabel_size
        self.ylabel = ylabel
        self.ylabel_size = ylabel_size
        self.figsize = figsize
        self.rotation_x = rotation_x
        self.rotation_y = rotation_y
        self.palette = palette
        self.showfliers = showfliers
        self.box_width = box_width
        self.ticklabel_size = ticklabel_size

    def generate(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        hue_col: str = None,
        ax=None,
        title: str = None,
        show_plot: bool = True,
        show_ylabel: bool = True,
        output_image_path: str = None,
    ):
        """
        Gera um boxplot único.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        sns.boxplot(
            data=data,
            x=x_col,
            y=y_col,
            hue=hue_col,
            ax=ax,
            palette=self.palette,
            width=self.box_width,
            showfliers=self.showfliers
        )

        ax.set_title(title or self.title, fontsize=self.title_size)
        ax.set_xlabel(self.xlabel or x_col, fontsize=self.xlabel_size, labelpad=20)
        
        if show_ylabel:
            ax.set_ylabel(self.ylabel or y_col, fontsize=self.ylabel_size, labelpad=20)
        else:
            ax.set_ylabel("")
            ax.set_yticklabels([])
            ax.tick_params(axis='y', length=0)

        ax.tick_params(axis='x', labelsize=self.ticklabel_size, rotation=self.rotation_x)
        ax.tick_params(axis='y', labelsize=self.ticklabel_size, rotation=self.rotation_y)

        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")

        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax


    def generate_multiboxplots(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        group_col: str,
        ax=None,
        palette=None,
        title: str = "",
        output_image_path: str = None,
        show_plot: bool = True
    ):
        """
        Gera boxplots agrupados por 'x_col' e diferenciados por 'group_col'.

        Exemplo: x = 'compressor', group = 'type' → boxplots de cada tipo por compressor.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        sns.boxplot(
            data=data,
            x=x_col,
            y=y_col,
            hue=group_col,
            ax=ax,
            palette=palette,
            showfliers=self.showfliers
        )
        sns.despine(trim=True)
        ax.set_title(title or self.title, fontsize=self.title_size)
        ax.set_xlabel(self.xlabel or x_col, fontsize=self.xlabel_size)
        ax.set_ylabel(self.ylabel or y_col, fontsize=self.ylabel_size)
        ax.tick_params(axis='x', rotation=self.rotation_x)

        ax.legend(title=group_col, loc='upper right')
        
        if output_image_path:
            ax.get_figure().savefig(output_image_path, bbox_inches='tight')
            print(f"Boxplot salvo em: {output_image_path}")

        if show_plot:
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
        Executa múltiplos plots com subplots (como múltiplos pares load/type).
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

        fig.suptitle(self.title or title, fontsize=self.title_size)

        plt.tight_layout()
        plt.subplots_adjust(top=0.80, bottom=0.1)  # Se precisar de mais espaço para title
        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")

        plt.show()
