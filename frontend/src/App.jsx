import { useEffect, useState } from 'react'

function App() {
  const [listings, setListings] = useState([])

  useEffect(() => {
    fetch('/listings')
      .then(res => res.json())
      .then(data => setListings(data))
      .catch(err => console.error('Error loading listings:', err))
  }, [])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Live Kijiji Listings</h1>
      {listings.length === 0 ? (
        <p>No listings found.</p>
      ) : (
        listings.map((item, index) => (
          <div
            key={index}
            style={{
              border: '1px solid #ccc',
              padding: '1rem',
              marginBottom: '1rem',
              borderRadius: '8px'
            }}
          >
            <h2>{item.title}</h2>

            {item.image && item.image !== "" && (
              <img
                src={item.image}
                alt={item.title}
                style={{
                  width: '100%',
                  height: '200px',
                  objectFit: 'cover',
                  borderRadius: '4px'
                }}
              />
            )}

            <p><strong>Posted:</strong> {new Date(item.timestamp).toLocaleString()}</p>
            <a href={item.url} target="_blank" rel="noopener noreferrer">View Listing</a>
          </div>
        ))
      )}
    </div>
  )
}

export default App