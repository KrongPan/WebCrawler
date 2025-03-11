<%@include file="configuration.jsp"%>
<%@page pageEncoding="UTF-8"%>
<html>
<head>
    <title><%= appTitle %></title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            text-align: center;
        }

        h1 {
            color: #333;
        }

        p {
            color: #555;
            font-size: 18px;
        }

        /* Centering the content */
        .container {
            width: 80%;
            margin: 0 auto;
        }

        /* Header styles */
        header {
            color: white;
            font-size: 20px;
            border-bottom: 3px solid #ddd;
        }

        /* Form styling */
        form {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-top: 30px;
        }

        form input[type="text"], form input[type="number"] {
            padding: 10px;
            width: 80%;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }

        form input[type="submit"] {
            background-color: #1a73e8;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        form input[type="submit"]:hover {
            background-color: #1558b0;
        }

        footer {
            margin-top: 20px;
            font-size: 14px;
            color: #777;
        }

        /* Responsive layout */
        @media (max-width: 768px) {
            .container {
                width: 100%;
                padding: 10px;
            }

            form input[type="text"], form input[type="number"] {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Section -->
        <header>
            <img src="<%= request.getContextPath() %>/images/thailand-1.jpg" alt="TH flag" style="width: 100%;" />
        </header>

        <!-- Main Content Section -->
        <form name="search" action="results.jsp" method="get">
            <h1>Welcome! Find your favorite places in Thailand.</h1>
            <p>
                <input name="query" type="text" placeholder="Enter place name or keyword" required />
            </p>
            <p>
                <input name="maxresults" type="number" value="10" /> Results Per Page
            </p>
            <p>
                <input type="submit" value="Search" />
            </p>
        </form>

    </div>
</body>
</html>
