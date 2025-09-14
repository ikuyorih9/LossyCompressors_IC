import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Times New Roman'
class BarPlot:
    def __init__(
        self,
        title:str="", 
        title_size:int = 16,
        xlabel:str = None, 
        xlabel_size:int = 16,
        ylabel:str = None, 
        ylabel_size:int = 16,

        xlim = [], 
        ylim=[],
        x = None,
        x_selected = None,
        y = None,
        sort = None,
        show_values:bool = True,
        bar_colors:str="blue",
        fmt:str = '%.1f',
        figsize = (12,8),
        loc='upper left', 
        bbox_to_anchor=(1.0, 1.0),
        layout=[0, 0, 1, 0.96]
    ):
        self.title = title
        self.title_size = title_size
        self.xlabel = xlabel
        self.xlabel_size = xlabel_size
        self.ylabel = ylabel
        self.ylabel_size = ylabel_size
        self.xlim = xlim
        self.ylim = ylim
        self.x = x
        self.x_selected = x_selected
        self.y = y
        self.sort = sort
        self.show_values = show_values
        self.bar_colors = bar_colors
        self.fmt = fmt
        self.figsize = figsize
        self.loc = loc
        self.bbox_to_anchor = bbox_to_anchor
        self.layout = layout

    def generate(
        self, 
        dataset:pd.DataFrame, 
        ax=None,
        x=None, 
        y=None,
        output_image_path:str = None, 
        title:str=None,
        show_ylabel: bool = True,
        show_plot:bool = True, 
        bar_colors=None
    ):
        """
        Gera um único gráfico de barras com base no dataset e colunas selecionadas.
        """

        if self.x is None or self.y is None:
            raise ValueError("x e y precisam ser definidos.")

        # Criação do gráfico
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_title(self.title if not title else title, pad=10,fontsize=self.title_size)
        ax.set_xlabel(self.xlabel if self.xlabel is not None else self.x,fontsize=self.xlabel_size)
        
        if show_ylabel:
            ax.set_ylabel(self.ylabel if self.ylabel is not None else self.y, fontsize=self.ylabel_size)
        else:
            ax.set_ylabel("")
            ax.set_yticklabels([])
            ax.tick_params(axis='y', length=0)

        if self.x_selected:
            dataset = dataset[dataset[self.x].isin(self.x_selected)]
        
        x = x if x else dataset[self.x] 
        y = y if y else dataset[self.y] 

        bars = ax.bar(x, y, color=bar_colors if bar_colors else self.bar_colors)

        if self.show_values:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    self.fmt % height,
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    rotation=45
                )

        if self.xlim:
            plt.xlim(self.xlim)
            ax.set_xlim(self.xlim)
        if self.ylim:
            plt.ylim(self.ylim)
            ax.set_ylim(self.ylim)

        # Rotacionar rótulos do eixo X
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")
        if show_plot:
            # fig.tight_layout(rect=[0, 0.0, 0.98, 1])
            plt.show()
        return ax

    
    def generate_multibars(self, dataset:pd.DataFrame, group_column: str, output_image_path:str = None, title:str=None, ax=None, show_plot:bool = True, bar_colors=None):
        """
        Gera gráfico de barras agrupadas, comparando múltiplas categorias para cada item de x_column.

        x_column: categorias no eixo X (ex: compressor)
        group_column: categorias das barras dentro do grupo (ex: type)
        value_column: valores das barras (ex: median_time)
        """

        df = dataset.copy()

        # Filtrar os dados antes de pivotar
        if self.x_selected:
            df = df[df[self.x].isin(self.x_selected)]

        if self.sort is not None:
            ascending = True if self.sort in ['asc', True] else False
            # ORDENAR PELO VALOR DE Y:
            df = df.sort_values(by=self.y, ascending=ascending)

            # Defina x como Categorical com a ordem desejada
            df[self.x] = pd.Categorical(df[self.x], categories=df[self.x].unique(), ordered=True)

        # Pivotar a tabela -> índice = compressor, colunas = type, valores = median_time
        pivot = df.pivot(index=self.x, columns=group_column, values=self.y)

        compressors = pivot.index.tolist()           # nomes no eixo X
        types = pivot.columns.tolist()               # 'API', 'MEMORY', 'PROCESS'
        x = np.arange(len(compressors))              # posição para grupos
        width = 0.8 / len(types)                     # largura de cada barra (dividindo espaço igualmente)
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize, constrained_layout=True)
        ax.set_title(self.title if not title else title, pad=10, fontsize=self.title_size)
        ax.set_xlabel(self.xlabel if self.xlabel else self.x, fontsize=self.xlabel_size)
        ax.set_ylabel(self.ylabel if self.ylabel else self.y, fontsize=self.ylabel_size)

        # Cores automáticas ou fixa
        if bar_colors:
            if isinstance(self.bar_colors, list):
                colors = bar_colors
            else:
                # Usa cor fixa ou gera paleta padrão
                colors = [bar_colors or "steelblue"] * len(types)
        else:
            if isinstance(self.bar_colors, list):
                colors = self.bar_colors
            else:
                # Usa cor fixa ou gera paleta padrão
                colors = [self.bar_colors or "steelblue"] * len(types)

        # Gera as barras para cada categoria do 'type'
        for i, tipo in enumerate(types):
            y = pivot[tipo].tolist()
            bar = ax.bar(x + i * width, y, width=width, label=tipo, color=colors[i % len(colors)])

            # Mostrar valores se necessário
            if self.show_values:
                for rect in bar:
                    height = rect.get_height()
                    ax.text(
                        rect.get_x() + rect.get_width() / 2,
                        height,
                        self.fmt % height,
                        ha='center',
                        va='bottom',
                        fontsize=9,
                        rotation=45
                    )

        # Configurar eixo X
        ax.set_xticks(x + width * (len(types) - 1) / 2)
        ax.set_xticklabels(compressors, rotation=45)

        if self.xlim:
            ax.set_xlim(self.xlim)
        if self.ylim:
            ax.set_ylim(self.ylim)

        ax.legend(title=group_column, loc=self.loc, bbox_to_anchor=self.bbox_to_anchor)
        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")
        if show_plot:
            fig.tight_layout(rect=[0, 0, 0.98, 1])
            plt.show()
        return ax
    
    def generate_multiplots(self, plot_functions: list, output_image_path:str = None, title:str=None, nrows=1, ncols=None):
        """
        Executa uma lista de funções de plotagem (plot_functions), cada uma desenhando em um Axes.

        Cada função deve aceitar um argumento `ax` e desenhar sobre ele.
        """
        num = len(plot_functions)
        if ncols is None:
            ncols = num
        if nrows * ncols < num:
            raise ValueError("nrows * ncols deve ser >= número de plots")

        fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(self.figsize[0] * ncols, self.figsize[1] * nrows))
        axs = axs.flatten() if isinstance(axs, np.ndarray) else [axs]

        for i, plot_fn in enumerate(plot_functions):
            ax = axs[i]
            plot_fn(ax)  # Aqui executamos a função de plot, repassando o ax

        # Desabilita eixos sobrando
        for i in range(len(plot_functions), len(axs)):
            fig.delaxes(axs[i])

        fig.tight_layout(rect=self.layout)
        plt.subplots_adjust(top=0.8)  # Se precisar de mais espaço para title
        plt.subplots_adjust(hspace=0.8)
        fig.suptitle(self.title if not title else title,fontsize=self.title_size)

        if output_image_path:
            fig.savefig(output_image_path, bbox_inches='tight')
            print(f"Imagem salva em: {output_image_path}")

        
        plt.show()
        






if __name__ == "__main__":
    # data = {
    #     'categoria': ['A', 'B', 'C', 'D'],
    #     'vendas_2020': [23, 45, 12, 34],
    #     'vendas_2021': [30, 44, 20, 40],
    #     'vendas_2022': [40, 50, 25, 48]
    # }
    # df = pd.DataFrame(data)
 
    df = pd.read_csv("../../13_python2_tests/damicore_time_stats.csv", sep='\t', decimal=',')
    df = df[df['load']=='ALL-COMPRESSORS_SERIAL']
    df = df[['load', 'type', 'compressor', 'median_time', 'median_process_time']]
    # print(df)

    # Exemplo: gráfico único
    bp1 = BarPlot(
        dataset=df[df['type']=='PROCESS'],
        title="Vendas em 2020",
        x='compressor',
        y='median_time',
        fmt='%.2f'
    )
    bp1.generate()

    bp2 = BarPlot(
        dataset=df,
        title="Tempo Mediano por Compressor e Tipo",
        xlabel="Compressor",
        x='compressor',
        y='median_time',
        ylabel="Tempo Mediano (s)",
        bar_colors=["#1f77b4", "#ff7f0e", "#2ca02c"],  # cores para API, MEMORY, PROCESS
        show_values=True
    )

    bp2.generate_multibars(
        group_column="type"
    )

    df_melted = df[df['type']=='PROCESS'].melt(
        id_vars=['compressor'],  # colunas que você quer manter fixas
        value_vars=['median_time', 'median_process_time'],  # colunas que viram “categorias”
        var_name='parameter',  # nova coluna para o nome da métrica
        value_name='value'     # nova coluna com os valores
    )

    print(df_melted)

    bp3 = BarPlot(
        dataset=df_melted,
        title="Tempo Mediano por Compressor e Tipo",
        xlabel="Compressor",
        x='compressor',
        y='value',
        ylabel="Tempo Mediano (s)",
        bar_colors=["#1f77b4", "#ff7f0e"],  # cores para API, MEMORY, PROCESS
        show_values=True
    )

    bp3.generate_multibars(
        group_column="parameter"
    )

    plots = [
        lambda ax: bp1.generate(ax=ax, show_plot=False),
        lambda ax: bp2.generate_multibars(ax=ax, group_column="type", show_plot=False),
        lambda ax: bp3.generate_multibars(ax=ax, group_column="parameter", show_plot=False)
    ]
    bp3.generate_multiplots(plot_functions=plots)
