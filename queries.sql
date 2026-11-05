-- 1. Which movie has the highest average MovieLens rating?
-- 1. Top 10 highest-rated movies
-- Minimum 50 ratings

SELECT
    m.movie_id,
    m.title,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM movies m
JOIN ratings r
    ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
ORDER BY average_rating DESC
LIMIT 1;


-- 2. What are the top 5 movie genres with the highest average rating?
SELECT
    g.genre_name,
    ROUND(AVG(r.rating), 2) AS average_rating,
    COUNT(r.rating) AS number_of_ratings
FROM genres AS g
JOIN movie_genres AS mg ON g.genre_id = mg.genre_id
JOIN ratings AS r ON mg.movie_id = r.movie_id
GROUP BY g.genre_id, g.genre_name
ORDER BY average_rating DESC, number_of_ratings DESC
LIMIT 5;


-- 3. Who is the director with the most movies in this dataset?
SELECT
    director,
    COUNT(*) AS movie_count
FROM omdb_details
WHERE director IS NOT NULL
  AND TRIM(director) <> ''
  AND director <> 'N/A'
GROUP BY director
ORDER BY movie_count DESC, director
LIMIT 1;


-- 4. What is the average rating of movies released each year?
SELECT
    m.release_year,
    ROUND(AVG(r.rating), 2) AS average_rating,
    COUNT(r.rating) AS number_of_ratings
FROM movies AS m
JOIN ratings AS r ON m.movie_id = r.movie_id
WHERE m.release_year IS NOT NULL
GROUP BY m.release_year
ORDER BY m.release_year;
