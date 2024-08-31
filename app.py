from dash.dependencies import Input, Output, State
import dash
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import ecom_rag
from ecom_rag import prod_inference, user_inference

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Define the layout for the home page
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Sample list of links with images
f = pd.read_json("assets/products.json")
product_name_list = list(f["product_name"])
links = [{'label': pro, 'href': '/' + pro.replace(" ", "_"), 'img_src': f'assets/{pro.replace(" ", "_")}.jpg'} for pro in product_name_list]


def get_product_rack_layout():
    # Create rows of 4 items each
    rows = []
    for i in range(0, len(links), 4):
        row_links = links[i:i+4]
        row_elements = [
            html.Div(
                [
                    html.Div(
                        html.Img(src=link['img_src'], style={'width': '100%', 'height': 'auto', 'borderRadius': '10px'}),
                        style={'width': '100px', 'height': '100px', 'overflow': 'hidden', 'marginBottom': '10px'}
                    ),
                    dcc.Link(link['label'], href=link['href'], style={
                        'display': 'block',
                        'textDecoration': 'none',
                        'color': '#333',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    })
                ],
                style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'backgroundColor': '#ffffff',
                    'padding': '15px',
                    'margin': '10px',
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)',
                    'transition': 'transform 0.3s ease, box-shadow 0.3s ease',
                    'width': '200px',
                    'cursor': 'pointer'
                },
                className='product-card'
            )
            for link in row_links
        ]
        rows.append(html.Div(row_elements, style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'}))

    return html.Div(
        [
            html.H2("Products", style={
                'textAlign': 'center',
                'color': '#333',
                'marginBottom': '30px',
                'fontWeight': 'bold',
                'fontSize': '28px',
                'borderBottom': '2px solid #ddd',
                'paddingBottom': '10px'
            }),
            *rows
        ],
        style={'flex': '7', 'backgroundColor': '#f9f9f9', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 8px 16px rgba(0, 0, 0, 0.1)'}
    )

# Define the layout for the home page
home_layout = html.Div([
    
    html.Div(
        [
            html.H1("Fractured Peaks", style={'textAlign': 'center', 'flex': '1'}),
            html.A(
                html.Div(
                    ' 👤 ',  # You can use any icon or text you like
                    style={
                        'width': '40px',
                        'height': '40px',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'borderRadius': '50%',
                        'backgroundColor': '#007BFF',
                        'color': '#FFFFFF',
                        'textDecoration': 'none',
                        'fontSize': '18px',
                        'fontWeight': 'bold'
                    }
                ),
                href='/user',  # Replace with the actual page URL
                style={
                    'marginRight': '10px'
                }
            )
        ],
        style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'padding': '10px'}
    ),

    html.Div(
        [
            get_product_rack_layout(),

            html.Div(
                [
                    html.H2("Chat Support", className='chat-support-header'),
                    html.Hr(),

                    # User input field
                    dcc.Input(id='user-input', type='text', value='', className='chat-input'),
                    
                    # Submit button
                    html.Button(
                        'Submit',
                        id='submit-button',
                        n_clicks=0,
                        className='chat-submit-button'
                    ),
                    
                    # Output area for chat history
                    html.Div(id='chat-history', className='chat-box')
                ],
                style={
                    'flex': '3',
                    'backgroundColor': '#f9f9f9',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'boxShadow': '0 8px 16px rgba(0, 0, 0, 0.1)',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center'
                }
            )
        ], style={'display': 'flex', 'height': '100%'} 
    ),
])

def get_product_page(pathname):
    img_path = "/assets/" + str(pathname) + ".jpg"

    f = pd.read_json("assets/products.json")
    f.set_index('product_name', inplace=True, drop=True)
    product_name = pathname.replace("_", " ")
    description = str(f.loc[product_name, "description"])
    price = str(f.loc[product_name, "price"])
    price = ''.join([char for char in price if char.isdigit() or char == "."])
    price = price.split('.')[0]

    page_layout = html.Div([
        html.H1(pathname.replace("_", " "), style={'textAlign': 'center'}),
        html.Hr(),

        html.Div([
            html.Div([
                html.Img(src=img_path, style={
                    'border': '2px solid #007BFF',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'backgroundColor': '#f9f9f9',
                    'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)',
                    'width': '80%',
                    'margin': '20px auto',
                }),
            ], style={'flex': '3', 'backgroundColor': '#d0d0d0', 'padding': '10px', 'textAlign': 'center'}),

            html.Div([
                html.Div([
                    html.H3("Price", style={'marginBottom': '10px'}),
                    html.P(price),
                    html.Hr(),
                    html.H3("Product Description", style={'marginBottom': '10px'}),
                    html.P(description),
                ], style={
                    'border': '2px solid #007BFF',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'backgroundColor': '#f9f9f9',
                    'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)',
                    'width': '80%',
                    'margin': '20px auto',
                }),
            ], style={'flex': '3', 'backgroundColor': '#d0d0d0', 'padding': '5px'}),

            html.Div([
                html.H1("Simple Chat Interface", style={'textAlign': 'center'}),
                html.Hr(),

                # User input field
                dcc.Input(id='user-input', type='text', value='', style={'width': '95%', 'margin': '10px'}),

                # Submit button
                html.Button(
                    'Submit',
                    id='submit-button',
                    n_clicks=0,
                    style={
                        'width': '150px',
                        'padding': '10px 20px',
                        'margin': '10px auto',
                        'display': 'block',
                        'backgroundColor': '#007BFF',
                        'color': '#FFFFFF',
                        'border': 'none',
                        'borderRadius': '5px',
                        'fontSize': '16px',
                        'fontWeight': 'bold',
                        'cursor': 'pointer',
                        'boxShadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',
                        'transition': 'background-color 0.3s ease'
                    }
                ),

                # Output area for chat history
                html.Div(id='chat-history', style={
                    'width': '95%',
                    'textAlign': 'left',
                    'marginTop': '20px',
                    'maxHeight': '400px',
                    'overflowY': 'auto',
                    'border': '1px solid #ccc',
                    'padding': '10px',
                    'backgroundColor': '#ffffff',
                    'borderRadius': '5px'
                })
            ], style={'flex': '3', 'backgroundColor': '#d0d0d0', 'padding': '5px'})
        ], style={'display': 'flex', 'height': '100%'}),

        html.Div(
            dcc.Link(
                'Back to Home', href='/', style={
                    'padding': '10px 20px',
                    'textAlign': 'center',
                    'color': '#FFFFFF',
                    'backgroundColor': '#007BFF',
                    'borderRadius': '8px',
                    'textDecoration': 'none',
                    'fontSize': '16px',
                    'fontWeight': 'bold',
                    'boxShadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',
                    'transition': 'background-color 0.3s ease'
                }),
            style={
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center',
                'height': '7vh',
            }
        )
    ])
    return page_layout

def get_user_order():
    # Load data
    f = pd.read_json("assets/user.json")
    f.set_index('product_name', inplace=True)

    f.drop_duplicates(inplace=True)
    # Debugging: Print DataFrame to verify content
    # print(f)

    # Define custom CSS styles
    table_style = {
        'width': '100%',
        'borderCollapse': 'collapse',
        'boxShadow': '0 5px 15px rgba(0, 0, 0, 0.1)',
    }
    header_style = {
        'backgroundColor': '#4CAF50',
        'color': 'white',
        'fontWeight': 'bold',
    }
    cell_style = {
        'padding': '12px 15px',
        'borderBottom': '1px solid #ddd',
        'textAlign': 'left',
    }
    row_even_style = {
        'backgroundColor': '#f2f2f2',
    }

    # Create table headers
    table_header = html.Thead(html.Tr([
        html.Th("Product Name", style=header_style), 
        html.Th("Price", style=header_style), 
        html.Th("Delivery Date", style=header_style),
        html.Th("Order Status", style=header_style), 
        html.Th("Location", style=header_style), 
        html.Th("Refundable", style=header_style)
    ]))

    # Create table rows
    table_rows = []
    for i, item in enumerate(f.index):
        # Debugging: Print each row to verify content
        print(f.loc[item])

        row_style = row_even_style if i % 2 == 0 else {}
        row = html.Tr([
            html.Td(item, style=cell_style),
            html.Td(f.loc[item, 'price'], style=cell_style),
            html.Td(f.loc[item, 'delivery_date'], style=cell_style),
            html.Td(f.loc[item, 'order_status'], style=cell_style),
            html.Td(f.loc[item, 'location'], style=cell_style),
            html.Td(f.loc[item, 'refundable'], style=cell_style),
        ], style=row_style)
        table_rows.append(row)

    # Combine header and rows into a table
    table_body = html.Tbody(table_rows)
    table = html.Table([table_header, table_body], style=table_style)

    return html.Div(
        [table],
        style={
            'width': '100%',  # Make the container div full-width
            'maxHeight': '400px',  # Set max height for the table container
            'overflowY': 'auto',  # Enable vertical scrolling
            'overflowX': 'auto',  # Enable horizontal scrolling
            'display': 'flex', 
            'justifyContent': 'center',  # Center the table horizontally
            'alignItems': 'center', 
            'padding': '10px',  # Adjusted padding
            'boxShadow': '0 5px 15px rgba(0, 0, 0, 0.1)',
        }
    )

def get_user_page():
    page_layout = html.Div([
        html.H1("HELLO! PARAMVEER", style={'textAlign': 'center'}),

        html.Div([
            html.Div([   
                html.H3("My Orders", style={'textAlign': 'center'}),
                html.Div([
                    get_user_order()
                ],style={'width': '100%', 'backgroundColor': '#f2f2f2', 'textAlign': 'center', 'padding': '10px', 'overflow': 'hidden'}),

                html.H3("My Reviews", style={'textAlign': 'center'}),
                html.Div([
                
                    html.Div([
                        html.H4("Product A", style={'marginBottom': '5px'}),
                        html.P("Great product! I really enjoyed using it. The quality is top-notch and it arrived on time.", style={'margin': '5px 0'}),
                        html.P("Rating: ★★★★☆", style={'color': '#FFD700', 'margin': '5px 0'})
                    ], style={'padding': '10px', 'borderBottom': '1px solid #ddd'}),

                    html.Div([
                        html.H4("Product B", style={'marginBottom': '5px'}),
                        html.P("Good value for money. The product does what it says. Would recommend to others.", style={'margin': '5px 0'}),
                        html.P("Rating: ★★★☆☆", style={'color': '#FFD700', 'margin': '5px 0'})
                    ], style={'padding': '10px', 'borderBottom': '1px solid #ddd'}),

                    html.Div([
                        html.H4("Product C", style={'marginBottom': '5px'}),
                        html.P("Not satisfied with the product. It didn't meet my expectations. The delivery was delayed.", style={'margin': '5px 0'}),
                        html.P("Rating: ★★☆☆☆", style={'color': '#FFD700', 'margin': '5px 0'})
                    ], style={'padding': '10px', 'borderBottom': '1px solid #ddd'})


                ],style={'width': '100%', 'backgroundColor': '#f2f2f2', 'textAlign': 'center', 'padding': '10px','overflow': 'hidden'}),
            ],style={'flex': '7', 'flexDirection': 'column', 'height': '100vh', 'justifyContent': 'center', 'alignItems': 'center', 'backgroundColor': '#e0e0e0'}),
            
            # Chat bot section
            html.Div([
                html.H3("Simple Chat Interface", style={'textAlign': 'center'}),
                html.Hr(),
                dcc.Input(id='user-input', type='text', value='', style={'width': '95%', 'margin': '10px'}),
                html.Button(
                    'Submit',
                    id='submit-button',
                    n_clicks=0,
                    style={
                        'width': '150px',
                        'padding': '10px 20px',
                        'margin': '10px auto',
                        'display': 'block',
                        'backgroundColor': '#007BFF',
                        'color': '#FFFFFF',
                        'border': 'none',
                        'borderRadius': '5px',
                        'fontSize': '16px',
                        'fontWeight': 'bold',
                        'cursor': 'pointer',
                        'boxShadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',
                        'transition': 'background-color 0.3s ease'
                    }
                ),
                html.Div(id='chat-history', style={
                    'width': '95%',
                    'textAlign': 'left',
                    'marginTop': '20px',
                    'maxHeight': '400px',
                    'overflowY': 'auto',
                    'border': '1px solid #ccc',
                    'padding': '10px',
                    'backgroundColor': '#ffffff',
                    'borderRadius': '5px'
                })
            ], style={'flex': '3', 'backgroundColor': '#d0d0d0', 'padding': '5px'})
        ], style={'display': 'flex', 'height': '100%'}),
    ])

    return page_layout

@app.callback(
    Output('chat-history', 'children'),
    [Input('url', 'pathname')],
    [Input('submit-button', 'n_clicks')],
    [State('user-input', 'value'),
     State('chat-history', 'children')]
)
def update_chat_history(url ,n_clicks, user_input, current_chat):
    if n_clicks > 0:
        if user_input:
            print("received user input on url:", url)
            url = str(url).lstrip('/')
            if "user" == url:
                response = user_inference(user_input,top_k=20,temperature=0.2,top_p=1.0,max_new_tokens=256)
                if 'initiate_refund' in response:
                    response += "(Product queued for refund)"
                if 'change_location' in response:
                    response += "(Product shipping location has been changed)"
            else:
                add_context = None
                if url is not None:
                    add_context = url.replace('_',' ')
                response = prod_inference(user_input,top_k=50,temperature=0.3,top_p=1.0,max_new_tokens=256,additional_context=add_context)
            new_message = html.Div(
                [
                    html.P(f"You: {user_input}", style={'margin': '5px 0', 'fontWeight': 'bold'}),
                    html.P(f"Bot: {response}", style={'margin': '5px 0'})
                ],
                style={'padding': '5px', 'borderBottom': '1px solid #ddd'}
            )

            if current_chat is None:
                current_chat = []

            return current_chat + [new_message]
    
    return []

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def update_page(pathname):
    pathname = pathname.lstrip("/").rstrip("/")
    if pathname == "":
        return home_layout
    elif pathname == "user":
        return get_user_page()
    else:
        return get_product_page(pathname)

if __name__ == '__main__':
    app.run_server(debug=False)
