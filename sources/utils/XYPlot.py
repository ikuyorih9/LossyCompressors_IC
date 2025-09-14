# xyplot.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
from adjustText import adjust_text  # certifique-se de instalar
from dataclasses import dataclass
from typing import List
import matplotlib.patches as mpatches
        
plt.rcParams['font.family'] = 'Times New Roman'

@dataclass
class Legend:
    title: str
    colors: List[str]
    texts: List[str]
    fontsize: int = 12

class XYPlot:
    def __init__(
        self,
        title: str = "",
        title_size: int = 14,
        xlabel: str = None,
        xlabel_size: int = 12,
        ylabel: str = None,
        ylabel_size: int = 12,
        figsize=(10, 8),
        rotation_x: int = 45,
        rotation_y: int = 0,
        legend: Legend = None,
        xlim: tuple = None,   # <<<<< NOVO
        ylim: tuple = None    # <<<<< NOVO
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
        self.legend = legend
        self.xlim = xlim
        self.ylim = ylim

    def lineplot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        hue: str = None,
        style: str = '-o',
        ax=None,
        output_image_path: str = None,
        show_plot: bool = True,
        title: str = None
    ):
        """
        Gera um gráfico de linha com múltiplas categorias (se 'hue' for fornecido).
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        if hue and hue in data.columns:
            for label, group in data.groupby(hue):
                ax.plot(group[x], group[y], style, label=str(label))
            ax.legend()
        else:
            ax.plot(data[x], data[y], style)

        # Ajustes visuais
        ax.set_title(title or self.title, fontsize=self.title_size, pad=20)
        ax.set_xlabel(self.xlabel or x, fontsize=self.xlabel_size)
        ax.set_ylabel(self.ylabel or y, fontsize=self.ylabel_size)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=self.rotation_x)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=self.rotation_y)

        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")
        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax

    # xyplot.py (acrescente à sua classe XYPlot)



    def scatterplot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        label_col: str,
        ax=None,
        output_image_path: str = None,
        show_plot: bool = True,
        title: str = None,
        point_style: dict = None,
        text_style: dict = None,
        use_adjust_text: bool = True,
        offset_x: float = 0.05,
        pound_x: int = 2,
        offset_y: float = 0.05,
        pound_y: int = 2,
        color_col: str = None,          # NOVO: coluna de cores
        show_grid: bool = True,          # NOVO: exibir grade
        log_x: bool = False,
        log_y: bool = False,
        show_legend: bool = True,
        show_labels: bool = True,
        show_ylabel: bool = True,
        marker: str = "o"
    ):
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        point_style = point_style or dict(s=50)
        text_style = text_style or dict(fontsize=10)

        # Plotando os pontos
        if "markers" in data.columns:
            for m, group in data.groupby("markers"):
                if color_col and color_col in group.columns:
                    ax.scatter(
                        group[x], group[y],
                        c=group[color_col],
                        marker=m,
                        **point_style
                    )
                else:
                    ax.scatter(
                        group[x], group[y],
                        marker=m,
                        **point_style
                    )
        else:
            if color_col and color_col in data.columns:
                ax.scatter(data[x], data[y], c=data[color_col], marker=marker, **point_style)
            else:
                ax.scatter(data[x], data[y], marker=marker, **point_style)

        # Adicionando os textos (labels)
        if show_labels:
            texts = []
            for i, row in data.iterrows():
                t = ax.annotate(
                    str(row[label_col]),
                    xy=(row[x], row[y]),             # ponto de verdade
                    xytext=(row[x]+ offset_x*(i % pound_x), row[y] + offset_y*(i % pound_y)),# posição inicial (espalha no Y)
                    textcoords='data',
                    ha='right', va='bottom',
                    arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
                    **text_style
                )
                texts.append(t)
            adjust_text(
                texts, ax=ax,
                expand_text=(0.5, 3.0),
                force_text=1,
                only_move={'points':'none', 'text':'xy'},  # autoriza mexer nos dois eixos
            )

        # Títulos e eixos
        ax.set_title(title or self.title, fontsize=self.title_size, pad=20)

        if show_ylabel:
            ax.set_ylabel(self.ylabel or y, fontsize=self.ylabel_size, labelpad=20)
        else:
            ax.set_ylabel("")
            ax.set_yticklabels([])
            ax.tick_params(axis='y', length=0)

        ax.set_xlabel(self.xlabel or x, fontsize=self.xlabel_size)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=self.rotation_x)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=self.rotation_y)

        if self.xlim:
            ax.set_xlim(self.xlim)
        if self.ylim:
            ax.set_ylim(self.ylim)

        if log_x:
            ax.set_xscale("log")

        if log_y:
            ax.set_yscale("log")

        if show_legend:
            if self.legend:
                title = self.legend.title
                colors = self.legend.colors
                texts = self.legend.texts
                
                patches = []
                for color,text in zip(colors,texts):
                    patches.append(mpatches.Patch(color=color, label=text))
                leg = ax.legend(handles=patches, title=title, loc="best", fontsize=self.legend.fontsize)
                leg.set_title(title =title,prop={'size': self.legend.fontsize})
            else:
                # Cria patches coloridos para legenda
                compressors = data[label_col].unique()
                handles = [
                    mpatches.Patch(
                        color=data[data[label_col] == comp][color_col].iloc[0],
                        label=comp
                    )
                    for comp in compressors
                ]
                ax.legend(handles=handles, title="Compressor", loc="best", fontsize=9)

        # Grade
        if show_grid:
            ax.minorticks_on()
            ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

        # Exportar ou mostrar
        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")

        if show_plot:
            plt.tight_layout()
            plt.show()

        return ax


    def generate_multiplots(
        self,
        plot_functions: list,  # lista de funções que recebem um ax
        output_image_path: str = None,
        title: str = None,
        nrows: int = 1,
        ncols: int = None
    ):
        """
        Gera múltiplos gráficos lado a lado ou em grade, usando funções que desenham em axes.
        """
        num = len(plot_functions)
        if ncols is None:
            ncols = num
        if nrows * ncols < num:
            raise ValueError("nrows * ncols deve ser >= número de plots")

        total_width = self.figsize[0] * ncols
        total_height = self.figsize[1] * nrows
        # fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(total_width, total_height))

        # axs = np.array(axs).flatten() if isinstance(axs, np.ndarray) else [axs]

        # for i, plot_fn in enumerate(plot_functions):
        #     plot_fn(axs[i])

        # # Remove eixos não utilizados
        # for i in range(len(plot_functions), len(axs)):
        #     fig.delaxes(axs[i])

        fig = plt.figure(figsize=(total_width, total_height))
        gs = fig.add_gridspec(nrows, ncols)

        axs = []
        i = 0
        while i < num:
            if i == num-1 and (num % ncols) == 1 and ncols > 1:
                # se sobrando só um plot na última linha, ele ocupa a linha inteira
                row = i // ncols
                ax = fig.add_subplot(gs[row, :])
            else:
                row = i // ncols
                col = i % ncols
                ax = fig.add_subplot(gs[row, col])
            axs.append(ax)
            i += 1

        for ax, plot_fn in zip(axs, plot_functions):
            plot_fn(ax) 

        fig.suptitle(title or self.title, fontsize=self.title_size)

        plt.tight_layout()
        plt.subplots_adjust(top=0.8)
        # plt.subplots_adjust(wspace=0.2)

        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")

        plt.show()

if __name__ == "__main__":
    # Dados de exemplo
    df = pd.DataFrame({
        "x": [1, 2, 3, 4],
        "y": [10, 15, 13, 17],
        "label": ["A", "B", "C", "D"]
    })

    # Instanciar o plotador
    plot = XYPlot(
        title="Scatter com Labels",
        xlabel="Eixo X",
        ylabel="Eixo Y",
        rotation_x=0,
        rotation_y=0
    )

    # Criar o gráfico
    plot.scatterplot(
    data=df,
    x="x",
    y="y",
    label_col="label",
    use_adjust_text=False,      # ou True, para reposicionamento automático
    offset_x=0.1,
    offset_y=0.05,
    point_style=dict(color='blue', s=80),
    text_style=dict(fontsize=12, color="black", fontweight="bold")
)
