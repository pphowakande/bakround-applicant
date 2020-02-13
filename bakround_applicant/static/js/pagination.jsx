import React from 'react';

function scrollToTop() {
    setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 0);
}

const Pagination = ({ firstItem, lastItem, countItems, pageClicked, jumpToTop }) =>
    <div className="pager">
      <span><b>showing {firstItem} to {lastItem}</b>{countItems ? ` (of ${countItems})` : ""}</span>&nbsp;
      <li className={firstItem > 1 ? '' : 'disabled'} style={firstItem > 1 ? {} : {pointerEvents: 'none'}}>
        <a style={{cursor: "pointer"}} onClick={() => {
            if (jumpToTop) scrollToTop();
            pageClicked('Previous');
        }}>Previous</a>
      </li>
      <li className={lastItem < countItems ? '' : 'disabled'} style={lastItem < countItems ? {} : {pointerEvents: 'none'}}>
        <a style={{cursor: "pointer"}} onClick={() => {
            if (jumpToTop) scrollToTop();
            pageClicked('Next');
        }}>Next</a>
      </li>
    </div>;

Pagination.defaultProps = {
    jumpToTop: false
};

export default Pagination;

